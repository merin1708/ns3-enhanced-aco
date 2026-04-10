#include "aco-routing-protocol.h"

#include "ns3/ipv4-l3-protocol.h"
#include "ns3/log.h"
#include "ns3/node-list.h"
#include "ns3/simulator.h"
#include "ns3/socket.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/wifi-net-device.h"

#include <map>

namespace ns3
{
NS_LOG_COMPONENT_DEFINE("AcoRoutingProtocol");

namespace aco
{

NS_OBJECT_ENSURE_REGISTERED(RoutingProtocol);
const uint32_t RoutingProtocol::ACO_PORT = 654;

RoutingProtocol::RoutingProtocol()
    : m_rreqRetries(2),
      m_ttlStart(1),
      m_ttlIncrement(2),
      m_ttlThreshold(7),
      m_timeoutBuffer(2),
      m_rreqRateLimit(10),
      m_rerrRateLimit(10),
      m_activeRouteTimeout(Seconds(3)),
      m_netDiameter(35),
      m_nodeTraversalTime(MilliSeconds(40)),
      m_netTraversalTime(Seconds(2.8)),
      m_pathDiscoveryTime(Seconds(5.6)),
      m_myRouteTimeout(Seconds(11.2)),
      m_helloInterval(Seconds(1)),
      m_allowedHelloLoss(2),
      m_deletePeriod(Seconds(15)),
      m_maxQueueLen(64),
      m_maxQueueTime(Seconds(30)),
      m_destinationOnly(false),
      m_gratuitousReply(true),
      m_enableHello(false),
      m_routingTable(m_deletePeriod),
      m_queue(m_maxQueueLen, m_maxQueueTime),
      m_requestId(0),
      m_seqNo(0),
      m_rreqIdCache(m_pathDiscoveryTime),
      m_dpd(m_pathDiscoveryTime),
      m_nb(Seconds(1)),
      m_rreqCount(0),
      m_rerrCount(0),
      m_htimer(Timer::CANCEL_ON_DESTROY),
      m_totalAntsSent(0),
      m_simulatedQueue(0),
      m_rreqRateLimitTimer(Timer::CANCEL_ON_DESTROY),
      m_rerrRateLimitTimer(Timer::CANCEL_ON_DESTROY)
{
    m_nb.SetCallback(MakeCallback(&RoutingProtocol::SendRerrWhenBreaksLinkToNextHop, this));
    m_discoveryStart = Seconds(0);
    m_currentEnergy = 75.0;
    m_esThreshold = 25.0;
    m_uniformRandomVariable = CreateObject<UniformRandomVariable>();
}

RoutingProtocol::~RoutingProtocol()
{
}

TypeId
RoutingProtocol::GetTypeId()
{
    static TypeId tid = TypeId("ns3::aco::RoutingProtocol")
                            .SetParent<Ipv4RoutingProtocol>()
                            .SetGroupName("Aco")
                            .AddConstructor<RoutingProtocol>();
    return tid;
}

void
RoutingProtocol::ScheduleFANTForward(Ptr<Socket> sock, Ptr<Packet> packet)
{
    if (sock)
    {
        sock->SendTo(packet, 0, InetSocketAddress(Ipv4Address::GetBroadcast(), ACO_PORT));
    }
}

void
RoutingProtocol::RouteRequestTimerExpire(Ipv4Address dst)
{
    m_addressReqTimer.erase(dst);
    RoutingTableEntry toDst;
    if (!m_routingTable.LookupRoute(dst, toDst))
    {
        if (toDst.GetRreqCnt() >= m_rreqRetries)
        {
            m_routingTable.DeleteRoute(dst);
            return;
        }
    }

    if (m_routingTable.LookupValidRoute(dst, toDst))
    {
        double rho = 0.2;
        double oldP = toDst.GetPheromone();
        double newP = oldP * (1.0 - rho);
        toDst.SetPheromone(newP);
        m_routingTable.Update(toDst);
    }

    if (m_queue.Find(dst))
    {
        SendRequest(dst);
        m_addressReqTimer[dst] =
            Simulator::Schedule(Seconds(1), &RoutingProtocol::RouteRequestTimerExpire, this, dst);
    }
}

Ptr<Ipv4Route>
RoutingProtocol::LoopbackRoute(const Ipv4Header& header, Ptr<NetDevice> oif) const
{
    NS_ASSERT(m_lo != nullptr);
    Ptr<Ipv4Route> route = Create<Ipv4Route>();
    route->SetDestination(header.GetDestination());
    if (header.GetSource() != Ipv4Address("127.0.0.1"))
    {
        route->SetSource(header.GetSource());
    }
    else
    {
        route->SetSource(m_ipv4->GetAddress(1, 0).GetLocal());
    }
    route->SetGateway(Ipv4Address("127.0.0.1"));
    route->SetOutputDevice(m_lo);
    return route;
}

Ptr<Socket>
RoutingProtocol::FindSocketWithInterfaceAddress(Ipv4InterfaceAddress iface) const
{
    for (const auto& iter : m_socketAddresses)
    {
        if (iter.second == iface)
        {
            return iter.first;
        }
    }
    return nullptr;
}

bool
RoutingProtocol::RouteInput(Ptr<const Packet> p,
                            const Ipv4Header& header,
                            Ptr<const NetDevice> idev,
                            const UnicastForwardCallback& ucb,
                            const MulticastForwardCallback& mcb,
                            const LocalDeliverCallback& lcb,
                            const ErrorCallback& ecb)
{
    Ipv4Address dst = header.GetDestination();

    if (m_ipv4->IsDestinationAddress(dst, m_ipv4->GetInterfaceForDevice(idev)))
    {
        if (idev != m_lo)
        {
            lcb(p, header, m_ipv4->GetInterfaceForDevice(idev));
            return true;
        }
    }

    if (idev == m_lo)
    {
        DeferredRouteOutput(p, header, ucb, ecb);
        return true;
    }

    RoutingTableEntry rt;
    if (m_routingTable.LookupValidRoute(dst, rt))
    {
        if (m_currentEnergy < m_esThreshold)
        {
            return false;
        }

        m_currentEnergy -= 0.010;

        Ptr<Ipv4Route> route = rt.GetRoute();
        ucb(route, p, header);
        return true;
    }
    return false;
}

void
RoutingProtocol::DeferredRouteOutput(Ptr<const Packet> p,
                                     const Ipv4Header& header,
                                     UnicastForwardCallback ucb,
                                     ErrorCallback ecb)
{
    Ipv4Address dst = header.GetDestination();
    RoutingTableEntry rt;

    QueueEntry newEntry(p, header, ucb, ecb);

    if (m_routingTable.LookupValidRoute(dst, rt))
    {
        Ptr<Ipv4Route> route = rt.GetRoute();
        ucb(route, p, header);
        return;
    }

    bool result = m_queue.Enqueue(newEntry);
    if (result && m_addressReqTimer.find(dst) == m_addressReqTimer.end())
    {
        SendRequest(dst);
        m_addressReqTimer[dst] =
            Simulator::Schedule(Seconds(1), &RoutingProtocol::RouteRequestTimerExpire, this, dst);
    }
}

Ptr<Ipv4Route>
RoutingProtocol::RouteOutput(Ptr<Packet> p,
                             const Ipv4Header& header,
                             Ptr<NetDevice> oif,
                             Socket::SocketErrno& sockerr)
{
    Ipv4Address dst = header.GetDestination();
    RoutingTableEntry rt;

    if (m_routingTable.LookupValidRoute(dst, rt))
    {
        m_currentEnergy -= 0.015;
        if (m_currentEnergy < m_esThreshold)
        {
            m_routingTable.DeleteRoute(dst);
            sockerr = Socket::ERROR_NOROUTETOHOST;
            return nullptr;
        }

        Ptr<Ipv4Route> route = rt.GetRoute();
        return route;
    }

    Ptr<Ipv4Route> route = LoopbackRoute(header, oif);
    if (route)
    {
        sockerr = Socket::ERROR_NOROUTETOHOST;
        return route;
    }

    sockerr = Socket::ERROR_NOROUTETOHOST;
    return nullptr;
}

void
RoutingProtocol::SendRequest(Ipv4Address dst)
{
    m_totalAntsSent++;
    m_discoveryStart = Simulator::Now();
    m_currentEnergy -= 0.005;

    Ipv4Address myIp = m_ipv4->GetAddress(1, 0).GetLocal();

    FantHeader fant;
    fant.SetOrigin(myIp);
    fant.SetDst(dst);
    fant.SetHopCount(0);
    fant.SetTotal3dDistance(0.0);
    fant.SetMinPathEnergy(m_currentEnergy);

    Ptr<Packet> packet = Create<Packet>();
    packet->AddHeader(fant);

    TypeHeader type(ACOTYPE_RREQ);
    packet->AddHeader(type);

    for (auto& j : m_socketAddresses)
    {
        Ptr<Socket> socket = j.first;
        Ptr<Packet> p = packet->Copy();
        socket->SendTo(p, 0, InetSocketAddress(Ipv4Address::GetBroadcast(), ACO_PORT));
    }
    NS_LOG_UNCOND("-> Drone " << myIp << " launched FANT looking for " << dst);
}

void
RoutingProtocol::RecvAco(Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    Address senderAddress;
    while ((packet = socket->RecvFrom(senderAddress)))
    {
        Ipv4Address sender = InetSocketAddress::ConvertFrom(senderAddress).GetIpv4();

        TypeHeader tHeader;
        packet->RemoveHeader(tHeader);

        Ipv4Address receiver = m_socketAddresses[socket].GetLocal();

        if (tHeader.Get() == ACOTYPE_RREQ)
        {
            RecvRequest(packet, receiver, sender);
        }
        else if (tHeader.Get() == ACOTYPE_RREP)
        {
            RecvReply(packet, receiver, sender);
        }
    }
}

void
RoutingProtocol::RecvRequest(Ptr<Packet> p, Ipv4Address receiver, Ipv4Address sender)
{
    FantHeader fant;
    p->RemoveHeader(fant);

    NS_LOG_UNCOND("<- " << receiver << " received FANT from " << sender << " originated by "
                        << fant.GetOrigin() << " looking for " << fant.GetDst());

    std::pair<Ipv4Address, Ipv4Address> cacheKey = std::make_pair(fant.GetOrigin(), fant.GetDst());
    if (m_fantCache.find(cacheKey) != m_fantCache.end() &&
        (Simulator::Now() - m_fantCache[cacheKey]).GetSeconds() < 1.0)
    {
        return;
    }
    m_fantCache[cacheKey] = Simulator::Now();

    fant.SetHopCount(fant.GetHopCount() + 1);

    if (m_currentEnergy < fant.GetMinPathEnergy())
    {
        fant.SetMinPathEnergy(m_currentEnergy);
    }

    RoutingTableEntry reverseRoute;
    if (!m_routingTable.LookupRoute(fant.GetOrigin(), reverseRoute))
    {
        RoutingTableEntry newRoute(m_ipv4->GetNetDevice(1),
                                   fant.GetOrigin(),
                                   true,
                                   1,
                                   m_ipv4->GetAddress(1, 0),
                                   fant.GetHopCount(),
                                   sender,
                                   Seconds(15.0));
        newRoute.SetPheromone(10.0);
        m_routingTable.AddRoute(newRoute);
    }
    else
    {
        reverseRoute.SetNextHop(sender);
        reverseRoute.SetHop(fant.GetHopCount());
        m_routingTable.Update(reverseRoute);
    }

    if (fant.GetDst() == receiver)
    {
        BantHeader bant;
        bant.SetOrigin(receiver);
        bant.SetDst(fant.GetOrigin());
        bant.SetPheromoneConcentration(100.0);

        Ptr<Packet> bantPacket = Create<Packet>();
        bantPacket->AddHeader(bant);
        TypeHeader type(ACOTYPE_RREP);
        bantPacket->AddHeader(type);

        Ptr<Socket> sock;
        for (const auto& iter : m_socketAddresses)
        {
            if (iter.second.GetLocal() == receiver)
            {
                sock = iter.first;
            }
        }
        if (sock)
        {
            sock->SendTo(bantPacket, 0, InetSocketAddress(sender, ACO_PORT));
        }

        NS_LOG_UNCOND("-> Destination " << receiver << " received FANT! Sending BANT to "
                                        << sender);
    }
    else if (receiver == Ipv4Address("10.1.1.16"))
    {
        NS_LOG_UNCOND("[ATTACK] Hacker Node 15 injecting malicious pheromone: 999.0");
        BantHeader bant;
        bant.SetOrigin(fant.GetDst());
        bant.SetDst(fant.GetOrigin());
        bant.SetPheromoneConcentration(999.0);

        Ptr<Packet> bantPacket = Create<Packet>();
        bantPacket->AddHeader(bant);
        TypeHeader type(ACOTYPE_RREP);
        bantPacket->AddHeader(type);

        Ptr<Socket> sock;
        for (const auto& iter : m_socketAddresses)
        {
            if (iter.second.GetLocal() == receiver)
            {
                sock = iter.first;
            }
        }
        if (sock)
        {
            sock->SendTo(bantPacket, 0, InetSocketAddress(sender, ACO_PORT));
        }
    }
    else
    {
        Ptr<Packet> fwdPacket = Create<Packet>();
        fwdPacket->AddHeader(fant);
        TypeHeader type(ACOTYPE_RREQ);
        fwdPacket->AddHeader(type);

        Ptr<Socket> sock;
        for (const auto& iter : m_socketAddresses)
        {
            if (iter.second.GetLocal() == receiver)
            {
                sock = iter.first;
            }
        }
        if (sock)
        {
            double jitterMs =
                m_uniformRandomVariable ? m_uniformRandomVariable->GetValue(0.0, 10.0) : 5.0;
            Simulator::Schedule(MilliSeconds(jitterMs),
                                &RoutingProtocol::ScheduleFANTForward,
                                this,
                                sock,
                                fwdPacket);
        }
    }
}

void
RoutingProtocol::RecvReply(Ptr<Packet> p, Ipv4Address receiver, Ipv4Address sender)
{
    BantHeader bant;
    p->RemoveHeader(bant);

    double T_max = 150.0;
    if (bant.GetPheromoneConcentration() > T_max)
    {
        NS_LOG_UNCOND("[SECURITY ALERT] Black Hole detected! Node "
                      << sender << " exceeds T_max...");
        return;
    }

    double D = 50.0;
    double d_decay = 0.5;
    double droneDensity = 5.0;
    double spatialAllowance = 10.0;
    double newPheromone =
        bant.GetPheromoneConcentration() / (2.0 * D * spatialAllowance * d_decay * droneDensity);

    bant.SetPheromoneConcentration(newPheromone);

    RoutingTableEntry route;
    if (!m_routingTable.LookupRoute(bant.GetOrigin(), route))
    {
        RoutingTableEntry newRoute(m_ipv4->GetNetDevice(1),
                                   bant.GetOrigin(),
                                   true,
                                   1,
                                   m_ipv4->GetAddress(1, 0),
                                   1,
                                   sender,
                                   Seconds(15.0));
        newRoute.SetPheromone(newPheromone);
        m_routingTable.AddRoute(newRoute);
    }
    else
    {
        route.SetPheromone(newPheromone);
        route.SetNextHop(sender);
        m_routingTable.Update(route);
    }

    if (bant.GetDst() == receiver)
    {
        NS_LOG_UNCOND("-> BANT returned to source! PDR Data Transmission can begin.");
        QueueEntry queueEntry;
        while (m_queue.Dequeue(bant.GetOrigin(), queueEntry))
        {
            DeferredRouteOutput(queueEntry.GetPacket(),
                                queueEntry.GetIpv4Header(),
                                queueEntry.GetUnicastForwardCallback(),
                                queueEntry.GetErrorCallback());
        }
    }
    else
    {
        RoutingTableEntry reverseRoute;
        if (m_routingTable.LookupRoute(bant.GetDst(), reverseRoute))
        {
            Ptr<Packet> fwdPacket = Create<Packet>();
            fwdPacket->AddHeader(bant);
            TypeHeader type(ACOTYPE_RREP);
            fwdPacket->AddHeader(type);

            Ptr<Socket> sock;
            for (const auto& iter : m_socketAddresses)
            {
                if (iter.second.GetLocal() == receiver)
                {
                    sock = iter.first;
                }
            }
            if (sock)
            {
                sock->SendTo(fwdPacket, 0, InetSocketAddress(reverseRoute.GetNextHop(), ACO_PORT));
            }
        }
    }
}

void
RoutingProtocol::SetIpv4(Ptr<Ipv4> ipv4)
{
    m_ipv4 = ipv4;
    m_lo = m_ipv4->GetNetDevice(0);
    Simulator::ScheduleNow(&RoutingProtocol::Start, this);
}

void
RoutingProtocol::NotifyInterfaceUp(uint32_t i)
{
    Ptr<Ipv4L3Protocol> l3 = m_ipv4->GetObject<Ipv4L3Protocol>();
    if (l3->GetNAddresses(i) > 0)
    {
        Ipv4InterfaceAddress iface = l3->GetAddress(i, 0);
        if (iface.GetLocal() == Ipv4Address("127.0.0.1"))
        {
            return;
        }

        Ptr<Socket> socket = Socket::CreateSocket(GetObject<Node>(), UdpSocketFactory::GetTypeId());
        NS_ASSERT(socket != nullptr);
        socket->SetRecvCallback(MakeCallback(&RoutingProtocol::RecvAco, this));
        socket->BindToNetDevice(l3->GetNetDevice(i));
        socket->Bind(InetSocketAddress(Ipv4Address::GetAny(), ACO_PORT));
        socket->SetAllowBroadcast(true);
        socket->SetIpRecvTtl(true);
        socket->SetIpTtl(1);
        m_socketAddresses.insert(std::make_pair(socket, iface));
    }
}

void
RoutingProtocol::NotifyAddAddress(uint32_t i, Ipv4InterfaceAddress address)
{
    Ptr<Ipv4L3Protocol> l3 = m_ipv4->GetObject<Ipv4L3Protocol>();
    if (!l3->IsUp(i))
    {
        return;
    }
    if (l3->GetNAddresses(i) == 1)
    {
        NotifyInterfaceUp(i);
    }
}

void
RoutingProtocol::Start()
{
    m_rreqRateLimitTimer.SetFunction(&RoutingProtocol::RreqRateLimitTimerExpire, this);
    m_rreqRateLimitTimer.Schedule(Seconds(1));
}

void
RoutingProtocol::NotifyInterfaceDown(uint32_t i)
{
}

void
RoutingProtocol::NotifyRemoveAddress(uint32_t i, Ipv4InterfaceAddress address)
{
}

void
RoutingProtocol::RreqRateLimitTimerExpire()
{
    m_rreqCount = 0;
    m_rreqRateLimitTimer.Schedule(Seconds(1));
}

void
RoutingProtocol::PrintRoutingTable(Ptr<OutputStreamWrapper> stream, Time::Unit unit) const
{
}

void
RoutingProtocol::DoDispose()
{
    for (auto& i : m_socketAddresses)
    {
        i.first->Close();
    }
    m_socketAddresses.clear();
    m_ipv4 = nullptr;
    Ipv4RoutingProtocol::DoDispose();
}

void
RoutingProtocol::DoInitialize()
{
}

bool
RoutingProtocol::UpdateRouteLifeTime(Ipv4Address addr, Time lifetime)
{
    return true;
}

void
RoutingProtocol::RecvError(Ptr<Packet> p, Ipv4Address src)
{
}

void
RoutingProtocol::RecvReplyAck(Ipv4Address neighbor)
{
}

void
RoutingProtocol::SendRerrWhenBreaksLinkToNextHop(Ipv4Address nextHop)
{
}

void
RoutingProtocol::ScheduleRreqRetry(Ipv4Address dst)
{
}

int64_t
RoutingProtocol::AssignStreams(int64_t stream)
{
    return 0;
}

} // namespace aco
} // namespace ns3
