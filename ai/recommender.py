from utils.logger import get_logger
from utils.config import RAM_WARNING_THRESHOLD, RAM_CRITICAL_THRESHOLD, SWAP_WARNING_THRESHOLD
from core.analyzer import run_analysis

logger = get_logger(__name__)

def generate_recommendations() -> list:
    # Run analysis and generate human-readable recommendations
    analysis = run_analysis()
    recommendations = []

    peak = analysis.get('peak_usage', {})
    average = analysis.get('average_usage', {})
    hogs = analysis.get('top_memory_hogs', [])
    leaks = analysis.get('suspected_leaks', [])

    # RAM peak recommendations
    if peak:
        if peak['percent_used'] >= RAM_CRITICAL_THRESHOLD:
            recommendations.append({
                'level': 'CRITICAL',
                'message': f"RAM peaked at {peak['percent_used']}% at {peak['timestamp']}. "
                           f"Immediate optimization recommended."
            })
        elif peak['percent_used'] >= RAM_WARNING_THRESHOLD:
            recommendations.append({
                'level': 'WARNING',
                'message': f"RAM peaked at {peak['percent_used']}% at {peak['timestamp']}. "
                           f"Consider closing unused applications."
            })

    # Average usage recommendations
    if average:
        if average['avg_percent'] >= RAM_WARNING_THRESHOLD:
            recommendations.append({
                'level': 'WARNING',
                'message': f"Average RAM usage is high at {average['avg_percent']}% "
                           f"over the last 24 hours. Consider upgrading RAM or reducing background apps."
            })
        else:
            recommendations.append({
                'level': 'INFO',
                'message': f"Average RAM usage is healthy at {average['avg_percent']}% "
                           f"over the last 24 hours."
            })

    # Swap usage recommendations
    if peak and peak.get('swap_percent', 0) >= SWAP_WARNING_THRESHOLD:
        recommendations.append({
            'level': 'WARNING',
            'message': f"Swap usage reached {peak['swap_percent']}%. "
                       f"High swap usage slows down your system significantly."
        })

    # Top memory hog recommendations
    if hogs:
        top = hogs[0]
        recommendations.append({
            'level': 'INFO',
            'message': f"'{top['name']}' is your top memory consumer with an average of "
                       f"{top['avg_memory_mb']} MB (peak: {top['max_memory_mb']} MB)."
        })

        if top['avg_memory_mb'] > 500:
            recommendations.append({
                'level': 'WARNING',
                'message': f"'{top['name']}' is consuming over 500 MB on average. "
                           f"Consider restarting or replacing it."
            })

    # Memory leak recommendations
    if leaks:
        for leak in leaks:
            recommendations.append({
                'level': 'CRITICAL',
                'message': f"Possible memory leak in '{leak['name']}': "
                           f"grew by {leak['growth_mb']} MB in the last hour "
                           f"({leak['min_mb']} MB → {leak['max_mb']} MB)."
            })

    # No issues found
    if not recommendations:
        recommendations.append({
            'level': 'INFO',
            'message': "System memory is running smoothly. No issues detected."
        })

    return recommendations

def print_recommendations():
    # Print all recommendations to terminal
    recommendations = generate_recommendations()

    logger.info("=" * 50)
    logger.info("SMART RECOMMENDATIONS")
    logger.info("=" * 50)

    for rec in recommendations:
        level = rec['level']
        msg = rec['message']

        if level == 'CRITICAL':
            logger.warning(f"[CRITICAL] {msg}")
        elif level == 'WARNING':
            logger.warning(f"[WARNING]  {msg}")
        else:
            logger.info(f"[INFO]     {msg}")

    logger.info("=" * 50)
    return recommendations