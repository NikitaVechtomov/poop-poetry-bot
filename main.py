import telebot

TELEGRAM_BOT_TOKEN = "5357340469:AAEfZl_2ODXEjimkkUnh4vmV2-vwLpbVTbc"
# CHAT_ID = 506643444

bot = telebot.TeleBot(token=TELEGRAM_BOT_TOKEN)

GAMES = {}

STAGES = 4

ARCHIVE = []


def _prettify(txt):
    return f"<i>***\n{txt}\n</i>"


def clear_game(game_id):
    ARCHIVE.append(GAMES.pop(game_id, None))


class Game:
    def __init__(self, host_id):
        self.game_id = host_id
        self.players = [host_id]
        self.stage = -1
        self.poems = {host_id: []}
        self.ready = {}
        self.seats = {}

    def add_player(self, player_id):
        self.players.append(player_id)
        self.poems[player_id] = []
        # notify everyone
        for plr_id in self.players:
            if plr_id != player_id:
                bot.send_message(plr_id, f"Игрок {player_id} присоединился к игре {self.game_id}")

    def get_current_poem_id(self, player_id):
        seat = self.seats[player_id]
        poem_no = (seat + self.stage) % len(self.players)
        return self.players[poem_no]

    def begin(self):
        # рассадка
        self.seats = {k: i for i, k in enumerate(self.players)}
        self.next_stage()

    def next_stage(self):
        self.stage += 1
        bot.send_message(self.game_id, f"Этап № {self.stage}")
        for player_id in self.players:
            self.ready[player_id] = False
            # первый раз пишем только одну строку
            if self.stage == 0:
                self.get_setup_line(None, player_id)
            else:
                self.get_punch_line(player_id)

    def get_setup_line(self, message_punch_line, player_id):
        if self.stage == 0:
            message = bot.send_message(player_id, "Придумай первую строчку. Например, 'вышел заяц на крыльцо...'")
        else:
            message = bot.send_message(player_id, "Придумай новую строчку")
        bot.register_next_step_handler(message, self.add_bars, player_id, line_no=1)

    def get_punch_line(self, player_id):
        prev_line = self.poems[self.get_current_poem_id(player_id)][-1]
        message = bot.send_message(player_id, f"Продолжи в рифму:\n{prev_line}\n...")
        bot.register_next_step_handler(message, self.add_bars, player_id, line_no=0)
        if self.stage < STAGES:
            bot.register_next_step_handler(message, self.get_setup_line, player_id)

    def add_bars(self, message, player_id, line_no):
        poem_id = self.get_current_poem_id(player_id)
        self.poems[poem_id].append(message.text)
        if (line_no == 1) or (self.stage == STAGES):
            self.ready[player_id] = True
            bot.send_message(player_id, "Ждём остальных участников...")
            if all(self.ready.values()):
                if self.stage == STAGES:
                    self.finish()
                else:
                    self.next_stage()

    def finish(self):
        poems = [_prettify("\n".join(poem)) for poem in self.poems.values()]
        all_poetry = "_____\n".join(poems)
        for player_id in self.players:
            bot.send_message(player_id, all_poetry, parse_mode="html")
        clear_game(self.game_id)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет!")


@bot.message_handler(commands=["new"])
def new_game(message):
    host_id = message.chat.id
    GAMES[host_id] = Game(host_id)
    bot.send_message(host_id, f"Игра с id {host_id} создана. Пригласи друзей и когда все будут готовы, напиши /begin")


@bot.message_handler(commands=["join"])
def join_game(message):
    msg = bot.send_message(message.chat.id, "Напиши id игры")
    bot.register_next_step_handler(msg, register_player)


def register_player(message):
    game_id = message.text
    if not game_id.isnumeric() or int(game_id) not in GAMES:
        bot.send_message(message.chat.id, "Ты куда звОнишь, ёбанарот?!")
    else:
        game_id = int(game_id)
        player_id = message.chat.id
        GAMES[game_id].add_player(player_id)
        bot.send_message(player_id, f"Вы присоединились, в комнате находятся игроки {GAMES[game_id].players}")


@bot.message_handler(commands=["begin"])
def begin(message):
    game_id = message.chat.id
    if game_id in GAMES:
        GAMES[game_id].begin()
    else:
        bot.send_message(game_id, f"Вы ещё не создали игру. Хотите создать новую? Напишите /new")


@bot.message_handler(commands=["info"])
def info(message):
    if len(GAMES) == 0:
        bot.send_message(message.chat.id, f"Сейчас нет активных игр. Хотите создать новую? Напишите /new")
    else:
        all_games = ", ".join(str(game) for game in GAMES)
        bot.send_message(message.chat.id, f"Список активных игр: {all_games}")


if __name__ == '__main__':
    bot.polling(none_stop=True)
