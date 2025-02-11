import aiohttp
import json
import matplotlib.pyplot as plt

from config import WEATHER_TOKEN


url_weather = "https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={token}"

def get_water_goal(weight, activity, weather):
    return float(30 * weight + 500 * activity // 30 + 500 * int(weather >= 25))


def get_cals_goal(weight, activity, height, age):
    return float(10 * weight + 6.25 * height - 5 * age + 200 * int(activity > 0))


async def get_weather(city):
    url = url_weather.format(city=city, token=WEATHER_TOKEN)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return float(json.loads(content)["main"]["temp"])


async def get_cals(product_name, weight):
    search_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            content = await response.json()
            product = content['products'][0]
            calories_per_100g = product['nutriments'].get('energy-kcal_100g', None)
            calories = (calories_per_100g * weight) / 100
            return calories

def plot_progress(water_logged, water_goal, calories_logged, calories_goal, burned_calories):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # График воды
    axes[0].bar(["Выпито", "Цель"], [water_logged, water_goal], color=['blue', 'lightblue'])
    axes[0].set_title("Прогресс по воде")
    axes[0].set_ylabel("Миллиграммы (мл)")
    axes[0].set_ylim(0, max(water_goal * 1.2, 1000))

    # График калорий
    consumed_calories = calories_logged - burned_calories  # Баланс калорий
    axes[1].bar(["Потреблено", "Цель"], [consumed_calories, calories_goal], color=['red', 'lightcoral'])
    axes[1].set_title("Прогресс по калориям")
    axes[1].set_ylabel("Калории (ккал)")
    axes[1].set_ylim(0, max(calories_goal * 1.2, 1000))

    # Сохранение изображения
    chart_path = "progress_chart.png"
    plt.savefig(chart_path)
    plt.close(fig)

    return chart_path

water_progress_template = """
Вода:
- Выпито: {0} мл из {1} мл.
- Осталось: {2} мл.
"""

cals_progress_template = """
Калории:
- Потреблено: {0} ккал из {1} ккал.
- Сожжено: {2} ккал.
- Баланс: {3} ккал.
"""