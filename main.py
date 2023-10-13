import random as rand
from datetime import date
import os
import asyncio
from aiogram.utils import executor
from aiogram import Dispatcher, Bot, types
from aiogram.types import MediaGroup,\
    InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

LOGO = 'https://wampi.ru/image/YcEmt2w'
TOKEN = '5973267086:AAE_HAGaVb1Dz-BbMNEwSAO-c5lRV6GonYI'
CHANNEL_USERNAME = '-1001979154769'
ADMIN_ID = '5254590818'
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
FAQ_txt = '''Площадка для продажи люксовой и "архивной" одежды.

Публикация вещей происходит через бота.

Вещи, которые не подходят под тематику паблика не публикуются.

По всем вопросам обращаться к администрации(@alexsbye).'''
POST_help = '''Форма для продажи:

Название:
В описании
Состояние:
Размер:
Цена:
Город:

(минимум 3 фото айтема, 2 из которых живые)

Форма для поиска:

Название: Ищу..
В описании
Состояние:
Размер:
Город:

1 фото максимум
(дополнительно можете указать и цену)'''



def on_startup(_):
    print('ЗАПУЩЕН')


async def set_default_commands(bot: Bot):
    await bot.set_my_commands([
        types.BotCommand("start", "Перезапустить бота"),
    ])

ikb_1 = InlineKeyboardMarkup()
b1_1 = InlineKeyboardButton('Подтвердить', callback_data='norm')
b2_1 = InlineKeyboardButton('Отменить', callback_data='nenorm')
ikb_1.add(b1_1).insert(b2_1)

kb = InlineKeyboardMarkup()
b1 = InlineKeyboardButton('FAQ',callback_data='FAQ')
b3 = InlineKeyboardButton('Как предложить пост', callback_data='how to post')
b4 = InlineKeyboardButton('Предложить пост', callback_data='post')
kb.add(b1).add(b3).insert(b4)

ikb_2 = InlineKeyboardMarkup()
b2_1 = InlineKeyboardButton('В меню', callback_data='back')
ikb_2.add(b2_1)

class post_up(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_res = State()


@dp.message_handler(commands='start', state='*')
async def st_hi(msg: types.Message, state: FSMContext):
    await msg.answer_photo(photo=LOGO, caption='Добро пожаловать!\nСвязь с админом: @alexsbye', reply_markup=kb)


@dp.callback_query_handler(lambda a: a.data == 'FAQ')
async def faaq(cal: types.CallbackQuery):
    await cal.message.answer(text=FAQ_txt, reply_markup=ikb_2)


@dp.callback_query_handler(lambda x: x.data == 'back')
async def menu(cal: types.CallbackQuery):
    await cal.message.answer_photo(photo=LOGO, caption='Добро пожаловать!\nСвязь с админом: @alexsbye', reply_markup=kb)


@dp.callback_query_handler(lambda a: a.data == 'how to post')
async def post_helpik(call: types.CallbackQuery):
    await call.message.answer(text=POST_help, reply_markup=ikb_2)


@dp.callback_query_handler(lambda a : a.data == 'post')
async def faq(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text='Название вашего товара')
    await state.set_state(post_up.waiting_for_name.state)


@dp.message_handler(content_types=['text'], state=post_up.waiting_for_name)
async def descript(msg: types.Message, state: FSMContext):
    valid = True
    for znak in ['/', '\\', '*', ':', '?', '|', '"', '<', '>']:
        if znak in msg.text:
            valid= False
            break
    if valid == True:
        global item_name
        item_name = msg.text
        await msg.answer(
            text='Отлично!А теперь назовите цену товара')
        await state.set_state(post_up.waiting_for_price.state)
    else:
        await msg.answer('не используйте специальные символы в поле название')
        state.finish()

@dp.message_handler(content_types=['text'], state=post_up.waiting_for_price)
async def price(msg: types.Message, state: FSMContext):
    global item_price
    if msg.text[-1].isdigit():
        item_price = msg.text + 'руб.'
    else:
        item_price = msg.text
    await msg.answer(text='Отлично!А теперь отправьте описание товара.')
    await state.set_state(post_up.waiting_for_description.state)

@dp.message_handler(content_types=['text'], state=post_up.waiting_for_description)
async def descript(msg: types.Message, state: FSMContext):
    global item_descript
    item_descript = msg.text
    global user_name
    user_name = msg.from_user.username
    await msg.answer(text='Отлично!А теперь отправьте фотографии товара.')
    await bot.send_message(chat_id=msg.chat.id, text=' После отправки не забудьте подтведить публикацию',
                           reply_markup=ikb_1)
    await state.set_state(post_up.waiting_for_photo.state)


@dp.message_handler(content_types=['photo'], state=post_up.waiting_for_photo)
async def process_photo(msg: types.Message, state: FSMContext):
    print(msg.photo[-1])
    global mkd_path
    mkd_path = fr'templ\{item_name}_{date.today()}'
    if not os.path.isdir(mkd_path):
        os.mkdir(mkd_path)
    photo_id = msg.photo[-1].file_id
    photoc = await bot.get_file(photo_id)
    await photoc.download(destination_file=f'{mkd_path}/{photo_id}.jpg')
    await state.finish()

@dp.message_handler(commands='cancel', state='*')
async def breaking(msg: types.Message, state: FSMContext):
    await msg.answer(text='Действие отменено')
    await state.finish()

@dp.callback_query_handler(lambda r: r.data == 'norm')
async def NORM(callback: types.CallbackQuery):
    global description
    description = f'''{item_name}\nЦена: {item_price}\n{item_descript}\n Автор поста: @{user_name}'''
    await send_photos_to_admin(ADMIN_ID, mkd_path, description)


@dp.callback_query_handler(lambda a: a.data == 'nenorm')
async def NENORM(call: types.CallbackQuery):
    await call.message.answer('публикация отменена', reply_markup=ikb_2)


async def send_photos_to_admin(admin_id, folder_path, description):
    files = os.listdir(folder_path)
    album = MediaGroup()
    if not files:
        return
    for photo in files:
        album.attach_photo(photo=InputFile(path_or_bytesio=f'{mkd_path}\\{photo}'))
    await bot.send_media_group(admin_id, media=album)
    await bot.send_message(ADMIN_ID, text=description, reply_markup=get_inline_keyboard())


def get_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton(text="Одобрить", callback_data="approve")
    cancel_button = types.InlineKeyboardButton(text="Отменить", callback_data="cancel")
    keyboard.add(approve_button, cancel_button)
    return keyboard


@dp.callback_query_handler(lambda callback_query: True)
async def handle_callback_query(callback_query: types.CallbackQuery):
    if callback_query.data == 'approve':
        await bot.send_message(callback_query.from_user.id, "Пост одобрен. Публикуем в канал...")
        await publish_to_channel(callback_query.from_user.id)
        await remove_folder(callback_query.from_user.id)
    elif callback_query.data == 'cancel':
        # Отмена - удаляем папку
        await bot.send_message(callback_query.from_user.id, "Пост отклонен. Удаляем папку...")
        await remove_folder(callback_query.from_user.id)
    await callback_query.answer()


async def publish_to_channel(admin_id):
    folder_path = mkd_path
    files = os.listdir(folder_path)
    album = MediaGroup()
    last = files[-1]
    if not files:
        return
    for photo in files:
        if photo != last:
            album.attach_photo(photo=InputFile(path_or_bytesio=f'{mkd_path}\\{photo}'))
        else:
            album.attach_photo(photo=InputFile(path_or_bytesio=f'{mkd_path}\\{photo}'), caption=description)
    await bot.send_media_group(CHANNEL_USERNAME, media=album)
    await bot.send_message(admin_id, "Пост успешно опубликован в канале.")


async def remove_folder(admin_id):
    files = os.listdir(mkd_path)
    for file in files:
        os.remove(os.path.join(mkd_path, file))
    os.rmdir(mkd_path)


if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=True)
