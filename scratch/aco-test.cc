#include "ns3/aco-helper.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/energy-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"
#include "ns3/wifi-radio-energy-model-helper.h"

using namespace ns3;
using namespace ns3::energy;

// Note: FANT/BANT routing headers and functions have been migrated to the interior of `ns3::aco::RoutingProtocol`.

int
main(int argc, char* argv[])
{
    uint32_t nNodes = 30; // Default to 30 nodes as per Paper Table 1
    CommandLine cmd;
    cmd.AddValue("nNodes", "Number of drones", nNodes);
    cmd.Parse(argc, argv);

    NodeContainer nodes;
    nodes.Create(nNodes);

    YansWifiPhyHelper wifiPhy;
    // Boost TxPower to increase Wi-Fi transmission range for the FANET
    wifiPhy.Set("TxPowerStart", DoubleValue(20.0)); 
    wifiPhy.Set("TxPowerEnd", DoubleValue(20.0));
    YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default();
    wifiPhy.SetChannel(wifiChannel.Create());
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);
    WifiMacHelper wifiMac;
    wifiMac.SetType("ns3::AdhocWifiMac");
    NetDeviceContainer devices = wifi.Install(wifiPhy, wifiMac, nodes);

    // --- NEW FANET ENERGY MODEL LOGIC ---

    // 1. Create the Battery (Basic Energy Source)
    BasicEnergySourceHelper basicSourceHelper;
    // Set the initial battery capacity (e.g., 10000 Joules)
    basicSourceHelper.Set("BasicEnergySourceInitialEnergyJ", DoubleValue(10000.0));

    // 2. Install the batteries onto all your drone nodes
    EnergySourceContainer eContainer = basicSourceHelper.Install(nodes);

    // 3. Create the Radio Energy Model (Tracking power used for Tx/Rx)
    WifiRadioEnergyModelHelper radioEnergyHelper;
    // You can adjust these values based on typical drone transmitter specs
    radioEnergyHelper.Set("TxCurrentA", DoubleValue(0.0174));    // Transmit current
    radioEnergyHelper.Set("RxCurrentA", DoubleValue(0.0197));    // Receive current
    radioEnergyHelper.Set("IdleCurrentA", DoubleValue(0.00027)); // Hovering/Idle current

    // 4. Attach the radio energy model to the Wi-Fi devices and the battery
    DeviceEnergyModelContainer deviceModels = radioEnergyHelper.Install(devices, eContainer);

    AcoHelper aco;
    InternetStackHelper stack;
    stack.SetRoutingHelper(aco);
    stack.Install(nodes);
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    // FIX: 50.0 meters allows neighbors to connect, but still forces multihop to reach the end!
    MobilityHelper mobility;
    mobility.SetPositionAllocator("ns3::GridPositionAllocator",
                                  "MinX",
                                  DoubleValue(0.0),
                                  "MinY",
                                  DoubleValue(0.0),
                                  "DeltaX",
                                  DoubleValue(50.0),
                                  "DeltaY",
                                  DoubleValue(50.0),
                                  "GridWidth",
                                  UintegerValue(5),
                                  "LayoutType",
                                  StringValue("RowFirst"));
    mobility.SetMobilityModel("ns3::ConstantVelocityMobilityModel");
    mobility.Install(nodes);

    // Target the furthest drone in the swarm (nNodes - 1)
    UdpEchoServerHelper echoServer(9);
    ApplicationContainer serverApps = echoServer.Install(nodes.Get(nNodes - 1));
    serverApps.Start(Seconds(1.0));
    serverApps.Stop(Seconds(10.0));

    UdpEchoClientHelper echoClient(interfaces.GetAddress(nNodes - 1), 9);
    echoClient.SetAttribute("MaxPackets", UintegerValue(5000));
    echoClient.SetAttribute("Interval", TimeValue(Seconds(0.2))); // Slowed down to 0.2 to prevent congestion
    echoClient.SetAttribute("PacketSize", UintegerValue(1024));

    ApplicationContainer clientApps = echoClient.Install(nodes.Get(0));
    clientApps.Start(Seconds(2.0));
    clientApps.Stop(Seconds(10.0));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    Simulator::Stop(Seconds(11.0));
    Simulator::Run();

    monitor->CheckForLostPackets();
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    double txPackets = 0, rxPackets = 0, rxBytes = 0, delaySum = 0;

    for (const auto& [id, stat] : stats)
    {
        txPackets += stat.txPackets;
        rxPackets += stat.rxPackets;
        rxBytes += stat.rxBytes;
        delaySum += stat.delaySum.GetSeconds();
    }

    double pdr = (txPackets > 0) ? (rxPackets / txPackets) * 100 : 0;
    double throughput = (rxBytes * 8) / (9.0 * 1e6);
    double avgDelay = (rxPackets > 0) ? (delaySum / rxPackets) * 1000 : 0;

    std::cout << "\n========================================================\n";
    std::cout << "            ACO FANET PERFORMANCE RESULTS\n";
    std::cout << "========================================================\n";
    std::cout << "Scenario: " << nNodes << " UAVs in 3D Mesh Topology\n";
    std::cout << "Flow 1 (Source: Node 0 -> Destination: Node " << (nNodes - 1) << ")\n";
    std::cout << "  > Tx Packets  : " << txPackets << "\n";
    std::cout << "  > Rx Packets  : " << rxPackets << "\n";
    std::cout << "  > Throughput  : " << throughput << " Mbps\n";
    std::cout << "  > Avg Delay   : " << avgDelay << " ms\n";
    std::cout << "--------------------------------------------------------\n";
    std::cout << " FINAL PDR (Packet Delivery Ratio): " << pdr << " %\n";
    std::cout << "========================================================\n" << std::endl;

    Simulator::Destroy();
    return 0;
}
