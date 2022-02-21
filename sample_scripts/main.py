from financespy.dashboards import open_dashboard

a = open_dashboard("/home/danilo/Documents/Finances/dashboards/monthly_dashboard.yaml")

print(a)
print(a.rows[0].charts[0].formula)
