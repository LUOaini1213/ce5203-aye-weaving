"""Read new SUMO outputs without consulting the historical result CSV."""
import statistics
import xml.etree.ElementTree as ET


def legacy_metrics(path, params, departed, arrived):
    """Preserve the archived runner's formulas for an explicit legacy comparison.

The report length is 373.01 m, not the shipped network's 357.32 m lane length.
The queue and capacity quantities below are proxies; see docs/REPRODUCTION.md.
"""
    free = params.free_speed
    length = params.report_weaving_length
    free_time = length / free
    delays, queues, speeds, excess, wait_proxy, flow_proxy = [], [], [], [], [], []
    net_loss = 0.0
    for interval in ET.parse(path).getroot().findall("interval"):
        edges = {e.attrib["id"]: e.attrib for e in interval.findall("edge")}
        if "E_weaving" in edges:
            e = edges["E_weaving"]
            density = float(e.get("density", 0))
            speed = float(e.get("speed", free))
            travel = float(e.get("traveltime", free_time))
            delays.append(max(0.0, travel - free_time))
            speeds.append(speed)
            queues.append(density * length / 1000 * max(0.0, 1 - speed / free))
            sampled = float(e.get("sampledSeconds", 0))
            if sampled > 0:
                wait_proxy.append(float(e.get("waitingTime", 0)) / (sampled / 60.0))
            flow = density * speed * 3.6
            excess.append(max(0.0, density * length / 1000 - flow * free_time / 3600))
        flow_proxy.append(sum(float(edges[e].get("density", 0)) *
                              float(edges[e].get("speed", free)) * 3.6
                              for e in ("E_main_out", "E_off_ramp") if e in edges))
        net_loss += sum(float(e.get("timeLoss", 0)) for e in edges.values())
    mean = lambda xs: statistics.mean(xs) if xs else 0.0
    peak = lambda xs: max(xs) if xs else 0.0
    return {
        "departed": departed, "arrived": arrived,
        "capacity_veh_h": round(peak(flow_proxy), 1),
        "throughput_veh_h": round(mean(flow_proxy), 1),
        "avg_delay_s_veh": round(mean(delays), 2),
        "peak_delay_s_veh": round(peak(delays), 2),
        "avg_queue_veh": round(mean(queues), 2),
        "peak_queue_veh": round(peak(queues), 2),
        "avg_time_in_queue_s_veh": round(mean(wait_proxy), 3),
        "avg_excess_acc_veh": round(mean(excess), 2),
        "peak_excess_acc_veh": round(peak(excess), 2),
        "net_total_timeloss_veh_s": round(net_loss, 1),
        "avg_speed_weaving_kmh": round(mean(speeds) * 3.6, 2),
        "avg_net_delay_s_veh": round(net_loss / max(1, departed), 2),
    }


def trip_metrics(path):
    trips = ET.parse(path).getroot().findall("tripinfo")
    completed = [t for t in trips if float(t.attrib["arrival"]) >= 0]
    return {
        "tripinfo_completed": len(completed),
        "tripinfo_unfinished": len(trips) - len(completed),
        "tripinfo_completed_time_loss_s": round(sum(float(t.attrib["timeLoss"]) for t in completed), 3),
        "tripinfo_completed_waiting_time_s": round(sum(float(t.attrib["waitingTime"]) for t in completed), 3),
        "tripinfo_completed_depart_delay_s": round(sum(float(t.attrib["departDelay"]) for t in completed), 3),
    }
