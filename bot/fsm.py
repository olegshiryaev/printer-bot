from aiogram.fsm.state import StatesGroup, State


class SearchFSM(StatesGroup):
    waiting_for_query = State()
    selecting_result = State()
