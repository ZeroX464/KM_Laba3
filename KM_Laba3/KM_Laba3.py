import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class InventorySystem:
    """Моделирование системы управления запасами (s, S)"""

    def __init__(self, s, S, start_amount=100, delivery_delay=2,
                 storage_cost_rate=1.0, fixed_order_expense=50.0, backlog_penalty=20.0):
        self.s = s
        self.S = S
        self.start_amount = start_amount
        self.current_stock = start_amount
        self.delivery_delay = delivery_delay
        self.storage_cost_rate = storage_cost_rate
        self.fixed_order_expense = fixed_order_expense
        self.backlog_penalty = backlog_penalty
        self.backlog_orders = []

        self.order_active = False
        self.arrival_day = None
        self.ordered_units = 0

        self.storage_daily = []
        self.order_expenses_daily = []
        self.penalty_daily = []
        self.stock_daily = []

    def process_day(self, required_today):
        if self.order_active and self.arrival_day == 0:
            self.current_stock += self.ordered_units
            self.order_active = False
            self.ordered_units = 0

        for backlog_demand in self.backlog_orders[:]:
            if backlog_demand <= self.current_stock:
                self.current_stock -= backlog_demand
                self.backlog_orders.remove(backlog_demand)

        if required_today <= self.current_stock:
            self.current_stock -= required_today
        else:
            self.backlog_orders.append(required_today - self.current_stock)
            self.current_stock = 0

        self.storage_daily.append(self.current_stock * self.storage_cost_rate)
        self.penalty_daily.append(sum(self.backlog_orders) * self.backlog_penalty)

        if not self.order_active and self.current_stock <= self.s:
            self.ordered_units = self.S - self.current_stock
            self.order_active = True
            self.arrival_day = self.delivery_delay
            self.order_expenses_daily.append(self.fixed_order_expense)
        else:
            self.order_expenses_daily.append(0.0)

        if self.order_active and self.arrival_day > 0:
            self.arrival_day -= 1

        self.stock_daily.append(self.current_stock)

    def total_cost(self):
        return sum(self.storage_daily) + sum(self.order_expenses_daily) + sum(self.penalty_daily)

    def service_level(self):
        days_without_shortage = sum(1 for c in self.penalty_daily if c == 0)
        return days_without_shortage / len(self.penalty_daily)

    def reset(self):
        self.current_stock = self.start_amount
        self.backlog_orders = []
        self.order_active = False
        self.arrival_day = None
        self.ordered_units = 0
        self.storage_daily = []
        self.order_expenses_daily = []
        self.penalty_daily = []
        self.stock_daily = []


np.random.seed(42)
days = 200
demand_sequence_main = np.random.poisson(lam=42, size=days)
demand_scale_factor = np.random.poisson(lam=1, size=days)
final_demand_sequence = demand_sequence_main * demand_scale_factor

print("Последовательность дневного спроса на продукцию:")
print(final_demand_sequence)

storage_cost_rate = np.random.randint(0, 10)
fixed_order_expense = np.random.randint(50, 300)
backlog_penalty = np.random.randint(10, 100)
delivery_delay = np.random.randint(1, 5)
start_amount = np.random.randint(50, 300)

def evaluate(s, S, demand_sequence, days, **kwargs):
    sys = InventorySystem(s, S, **kwargs)
    for demand_value in demand_sequence[:days]:
        sys.process_day(demand_value)
    return sys.total_cost() / days, sys

s_range = range(10, 200, 20)
S_range = range(20, 400, 20)

best_cost = float('inf')
best_s, best_S = None, None
best_sys = None

data = []

for s in s_range:
    for S in S_range:
        if s >= S:
            continue
        cost_per_day, sys_obj = evaluate(s, S, final_demand_sequence, days,
                                         start_amount=start_amount,
                                         delivery_delay=delivery_delay,
                                         storage_cost_rate=storage_cost_rate,
                                         fixed_order_expense=fixed_order_expense,
                                         backlog_penalty=backlog_penalty)
        total = sys_obj.total_cost()
        sum_order = sum(sys_obj.order_expenses_daily)
        sum_holding = sum(sys_obj.storage_daily)
        sum_shortage = sum(sys_obj.penalty_daily)
        
        data.append([s, S, total, sum_order, sum_holding, sum_shortage, cost_per_day])

        if cost_per_day < best_cost:
            best_cost = cost_per_day
            best_s, best_S = s, S
            best_sys = sys_obj

df = pd.DataFrame(data, columns=['s', 'S', 'Общие затраты', 'Затраты на заказы', 'Затраты на хранение', 'Затраты на дефицит', 'Средние в день'])

print("\nТаблица сравнения параметров (s, S)")
print(df.to_string(index=False))

print("\nПоиск оптимальных параметров")
print(f"Лучшие параметры: s = {best_s}, S = {best_S}")
print(f"Минимальные средние затраты в день: {best_cost:.2f} руб.")

print(f"\nРезультаты моделирования (s={best_s}, S={best_S})")
print(f"Время доставки: {delivery_delay} д.")
print(f"Суммарные затраты: {best_sys.total_cost():.2f} руб.")
print(f"Уровень обслуживания: {best_sys.service_level():.2%}")
print(f"Средний запас: {np.mean(best_sys.stock_daily):.1f} ед.")

plt.figure(figsize=(12, 4))
plt.plot(best_sys.stock_daily, label='Уровень запасов')
plt.axhline(y=best_sys.s, color='r', linestyle='--', label='s (точка заказа)')
plt.axhline(y=best_sys.S, color='g', linestyle='--', label='S (максимум)')
plt.xlabel('День')
plt.ylabel('Запас')
plt.title(f'Динамика запасов при оптимальной стратегии (s={best_s}, S={best_S})')
plt.legend()
plt.grid(True)
plt.show()