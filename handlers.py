import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from states import Form

from utils import (
    get_cals_goal,
    get_water_goal,
    get_weather,
    get_cals,
    water_progress_template,
    cals_progress_template,
    plot_progress
)

bot_router = Router()

data_storage = {}
user_id_counter = 0

async def store_user_data(user_data):
    temp = await get_weather(user_data["city"])
    water_target = get_water_goal(user_data["weight"], user_data["activity_minutes"], temp)
    calorie_target = get_cals_goal(user_data["weight"], user_data["activity_minutes"], user_data["height"], user_data["age"])

    global user_id_counter, data_storage
    data_storage[user_id_counter] = {
        **user_data,
        "water_goal": water_target,
        "calories_goal": calorie_target,
        "logged_water": 0.0,
        "logged_calories": 0.0,
        "burned_calories": 0.0,
    }

@bot_router.message(Command("start"))
async def welcome_user(message: Message):
    await message.reply("Приветствую! Я ваш помощник по здоровому образу жизни.")

@bot_router.message(Command("set_profile"))
async def request_weight(message: Message, state: FSMContext):
    await message.answer("Введите ваш вес (кг):")
    await state.set_state(Form.weight)

@bot_router.message(Form.weight)
async def handle_weight(message: Message, state: FSMContext):
    try:
        weight_value = float(message.text)
    except ValueError:
        await message.reply("Некорректное значение веса. Попробуйте снова.")
        return

    await state.update_data(weight=weight_value)
    await message.answer("Введите ваш рост (см):")
    await state.set_state(Form.height)

@bot_router.message(Form.height)
async def handle_height(message: Message, state: FSMContext):
    try:
        height_value = float(message.text)
    except ValueError:
        await message.reply("Некорректное значение роста. Попробуйте снова.")
        return

    await state.update_data(height=height_value)
    await message.answer("Введите ваш возраст:")
    await state.set_state(Form.age)

@bot_router.message(Form.age)
async def handle_age(message: Message, state: FSMContext):
    try:
        age_value = int(message.text)
    except ValueError:
        await message.reply("Некорректный возраст. Попробуйте снова.")
        return

    await state.update_data(age=age_value)
    await message.answer("Сколько минут вы активны ежедневно?")
    await state.set_state(Form.activity_minutes)

@bot_router.message(Form.activity_minutes)
async def handle_activity(message: Message, state: FSMContext):
    try:
        active_minutes = float(message.text)
    except ValueError:
        await message.reply("Некорректное количество минут активности. Попробуйте снова.")
        return

    await state.update_data(activity_minutes=active_minutes)
    await message.answer("Введите название вашего города:")
    await state.set_state(Form.city)

@bot_router.message(Form.city)
async def handle_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Ваши параметры сохранены!")
    user_data = await state.get_data()
    await store_user_data(user_data)
    await state.clear()

@bot_router.message(Command("log_water"))
async def track_water_intake(message: Message, command: CommandObject):
    try:
        consumed_water = float(command.args)
    except (AttributeError, ValueError):
        await message.reply("Введите корректное количество выпитой воды.")
        return

    data_storage[user_id_counter]["logged_water"] += consumed_water
    await message.answer(f'Всего выпито: {data_storage[user_id_counter]["logged_water"]} мл. Цель: {data_storage[user_id_counter]["water_goal"]} мл.')

@bot_router.message(Command("log_food"))
async def track_food_intake(message: Message, command: CommandObject):
    try:
        food_name, weight = command.args.split(" ")
        weight = float(weight)
    except (AttributeError, ValueError):
        await message.reply("Введите корректные данные о продукте и его весе.")
        return

    calorie_value = await get_cals(food_name, weight)
    data_storage[user_id_counter]["logged_calories"] += calorie_value
    await message.answer(f"{food_name} - {weight} г. : {calorie_value} ккал.")

@bot_router.message(Command("log_workout"))
async def track_workout(message: Message, command: CommandObject):
    try:
        workout, duration = command.args.split(" ")
        duration = float(duration)
    except (AttributeError, ValueError):
        await message.reply("Введите корректные данные о тренировке.")
        return

    data_storage[user_id_counter]["burned_calories"] += 300
    additional_water = f" Дополнительно выпейте {200 * (duration // 30)} мл воды." if duration >= 30 else ""
    await message.answer(f"{workout} {duration} минут — 300 ккал.{additional_water}")

@bot_router.message(Command("check_progress"))
async def show_progress(message: Message):
    try:
        user_data = data_storage[user_id_counter]

        await message.answer(
            water_progress_template.format(
                user_data["logged_water"],
                user_data["water_goal"],
                max(user_data["water_goal"] - user_data["logged_water"], 0),
            )
        )

        await message.answer(
            cals_progress_template.format(
                user_data["logged_calories"],
                user_data["calories_goal"],
                user_data["burned_calories"],
                user_data["logged_calories"] - user_data["burned_calories"],
            )
        )

        chart_path = plot_progress(
            user_data["logged_water"],
            user_data["water_goal"],
            user_data["logged_calories"],
            user_data["calories_goal"],
            user_data["burned_calories"]
        )

        photo = FSInputFile(chart_path)
        await message.answer_photo(photo, caption="Вот ваш прогресс!")

        os.remove(chart_path)

    except KeyError:
        await message.answer("Ошибка: Данные не найдены. Сначала установите профиль с помощью /set_profile.")

def register_handlers(dispatcher):
    dispatcher.include_router(bot_router)
