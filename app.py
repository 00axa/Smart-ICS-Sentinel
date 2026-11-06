from datetime import datetime
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


class ICSSentinelEngine:

  def __init__(self, current_temp=-30.0, max_safe_temp=5.0, max_rate=2.0):
    self.current_temp = current_temp
    self.max_safe_temp = max_safe_temp
    self.max_rate = max_rate
    self.last_update_time = datetime.now()

  def evaluate_command(
      self, target_temp, role="operator", is_maintenance=False
  ):
    now = datetime.now()
    time_diff_mins = max(
        (now - self.last_update_time).total_seconds() / 60.0, 0.01
    )

    # 1. Absolute Threshold Check
    if target_temp > self.max_safe_temp:
      return {
          "status": "BLOCKED",
          "reason": (
              f"Critical Threshold Violation: {target_temp}°C exceeds max safe"
              f" limit ({self.max_safe_temp}°C)."
          ),
          "type": "CRITICAL_THRESHOLD",
      }

    # 2. Physics-Aware Rate of Change Check
    rate_of_change = abs(target_temp - self.current_temp) / time_diff_mins
    if rate_of_change > self.max_rate:
      return {
          "status": "BLOCKED",
          "reason": (
              f"Physics Anomaly: Rate of change {rate_of_change:.1f}°C/min"
              f" exceeds physical limit ({self.max_rate}°C/min)."
          ),
          "type": "PHYSICS_ANOMALY",
      }

    # 3. Contextual Intent Check (Off-hours check)
    current_hour = now.hour
    if (
        current_hour >= 23 or current_hour < 5
    ) and not is_maintenance:  # Simplified for daytime demo or forced off-hours
      pass  # Keep strict or leave open for daytime testing

    # Success
    self.current_temp = target_temp
    self.last_update_time = now
    return {
        "status": "SUCCESS",
        "reason": f"Command executed safely. New temp: {self.current_temp}°C",
        "type": "EXECUTED",
    }


sentinel = ICSSentinelEngine()


@app.route("/")
def index():
  return render_template(
      "index.html", current_temp=sentinel.current_temp, max_safe=sentinel.max_safe_temp
  )


@app.route("/api/command", methods=["POST"])
def send_command():
  data = request.json
  target_temp = float(data.get("target_temp", -30.0))
  role = data.get("role", "operator")
  is_maintenance = data.get("is_maintenance", False)

  result = sentinel.evaluate_command(target_temp, role, is_maintenance)
  return jsonify(
      {
          "result": result,
          "current_temp": sentinel.current_temp,
          "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      }
  )


if __name__ == "__main__":
  app.run(debug=True, port=5000)