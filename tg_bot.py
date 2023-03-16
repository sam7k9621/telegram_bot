import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
import logging 


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class Backery:
    def __init__(self, token):
        self.manager = Application.builder().token(token).build()
        # State
        self.MENU, self.WAREHOUSE, self.INVENTORY, self.COMMODITY, self.STORE, self.NUMBER = range(6)
        # Handler
        self.menu_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            fallbacks=[CommandHandler("start", self.start)],
            states={
                self.MENU: [
                    CallbackQueryHandler(self.stock_menu, pattern="inventory$"),
                    CallbackQueryHandler(self.trade_menu, pattern="purchase"),
                    CallbackQueryHandler(self.revenue, pattern="revenue"),
                    CallbackQueryHandler(self.reset, pattern="reset"),
                ],
                self.WAREHOUSE: [
                    CallbackQueryHandler(self.add_stock, pattern="insert"),
                    CallbackQueryHandler(self.show, pattern="list"),
                    CallbackQueryHandler(self.user_menu, pattern="back"),
                ],
                self.INVENTORY: [
                    CallbackQueryHandler(self.stock, pattern="[0-9]+"),
                    CallbackQueryHandler(self.stock_menu, pattern="done"),
                ],
                self.STORE: [
                    CallbackQueryHandler(self.add_buy, pattern="purchase"),
                    CallbackQueryHandler(self.coupon, pattern="coupon"),
                    CallbackQueryHandler(self.coupon, pattern="decoupon"),
                    CallbackQueryHandler(self.user_menu, pattern="back"),
                ],
                self.COMMODITY: [
                    CallbackQueryHandler(self.stock, pattern="[0-9]+"),
                    CallbackQueryHandler(self.trade_menu, pattern="done"),
                ],
                self.NUMBER: [
                    CallbackQueryHandler(self.number, pattern="[<0-9]"),
                    CallbackQueryHandler(self.enter_amount, pattern="enter"),
                ],
            },
        )
       
        # Add ConversationHandler to application that will be used for handling updates
        self.manager.add_handler(self.menu_handler)

    def start_to_work(self):
        # Run the bot until the user presses Ctrl-C
        self.manager.run_polling()

    # menu
    def init(self, context) -> None:
        self.load_menu()

        context.user_data["stock"] = {}
        context.user_data["order"] = {}
       
        context.user_data["item"] = ""
        context.user_data["number"] = ""
        context.user_data["is_trade"] = False
        context.user_data["use_coupon"] = False
        context.user_data["not_enough"] = False
        context.user_data["bill"] = 0
        context.user_data["revenue"] = 0

        context.user_data["number_keyboard"] = [
            [
                InlineKeyboardButton("1", callback_data="1"),
                InlineKeyboardButton("2", callback_data="2"),
                InlineKeyboardButton("3", callback_data="3")
            ],
            [
                InlineKeyboardButton("4", callback_data="4"),
                InlineKeyboardButton("5", callback_data="5"),
                InlineKeyboardButton("6", callback_data="6")
            ],
            [
                InlineKeyboardButton("7", callback_data="7"),
                InlineKeyboardButton("8", callback_data="8"),
                InlineKeyboardButton("9", callback_data="9")
            ],
            [
                InlineKeyboardButton("0", callback_data="0"),
                InlineKeyboardButton("BS", callback_data="<"),
            ],
            [
                InlineKeyboardButton("輸入", callback_data="enter")
            ]
        ]
        context.user_data["menu_keyboard"] = [
            [
                InlineKeyboardButton("庫存", callback_data="inventory")
            ],
            [
                InlineKeyboardButton("購買", callback_data="purchase")
            ],
            [
                InlineKeyboardButton("收入", callback_data="revenue")
            ],
            [
                InlineKeyboardButton("重設", callback_data="reset")
            ],
        ]
        context.user_data["warehouse_keyboard"] = [
            [
                InlineKeyboardButton("新增", callback_data="insert")
            ],
            [
                InlineKeyboardButton("盤點", callback_data="list")
            ],
            [
                InlineKeyboardButton("上一頁", callback_data="back")
            ],
        ]
        context.user_data["inventory_keyboard"] = [
            [InlineKeyboardButton(info["name"], callback_data=idx)] for idx, info in sorted(self.store_menu.items())  


            # [
                # InlineKeyboardButton("巧克麵包", callback_data="0"),
            # ],
            # [
                # InlineKeyboardButton("松露麵包", callback_data="1"),
            # ],
            # [
                # InlineKeyboardButton("完成", callback_data="done"),
            # ]
        ]
        context.user_data["commodity_keyboard"] = [
            [
                InlineKeyboardButton("巧克麵包", callback_data="0"),
            ],
            [
                InlineKeyboardButton("松露麵包", callback_data="1"),
            ],
            [
                InlineKeyboardButton("完成", callback_data="done"),
            ]
        ]

    def load_menu(self):
        with open("menu.json", "r", encoding='utf8') as f:
            self.store_menu = json.load(f)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        logger.info("User %s started the conversation.", user.first_name)

        self.init(context) 
        reply_markup = InlineKeyboardMarkup(context.user_data["menu_keyboard"])
        await update.message.reply_text("你想做啥？", reply_markup=reply_markup)
        return self.MENU

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        self.init(context)
        return await self.user_menu(update, context)

    async def user_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        reply_markup = InlineKeyboardMarkup(context.user_data["menu_keyboard"])
        await query.edit_message_text(text="你想做啥？", reply_markup=reply_markup)
        return self.MENU
    
    async def revenue(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        reply_markup = InlineKeyboardMarkup(context.user_data["menu_keyboard"])
        await query.edit_message_text(text=f"{context.user_data['revenue']}", reply_markup=reply_markup)
        return self.MENU

    async def stock_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, content="想對庫存做啥？") -> int:
        query = update.callback_query
        await query.answer()
       
        context.user_data["is_trade"] = False

        reply_markup = InlineKeyboardMarkup(context.user_data["warehouse_keyboard"])
        await query.edit_message_text(text=content, reply_markup=reply_markup)
        return self.WAREHOUSE
    
    async def trade_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
      
        self.checkout(context) 
        context.user_data["is_trade"] = True

        store_keyboard = [
                [
                    InlineKeyboardButton("直接購買", callback_data="purchase"),
                ],
                [
                    InlineKeyboardButton("上一頁", callback_data="back"),
                ],
            ]
        if context.user_data["use_coupon"]:
            store_keyboard.insert(0, [InlineKeyboardButton("取消優惠", callback_data="decoupon")])
        else:
            store_keyboard.insert(0, [InlineKeyboardButton("使用優惠", callback_data="coupon")])

        reply_markup = InlineKeyboardMarkup(store_keyboard)
        await query.edit_message_text(text="在店裡想幹嘛?", reply_markup=reply_markup)
        return self.STORE

    async def add_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        
        reply_markup = InlineKeyboardMarkup(context.user_data["inventory_keyboard"])
        await query.edit_message_text(text="更新你的庫存", reply_markup=reply_markup)
        return self.INVENTORY
         
    async def add_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE, not_enough=False) -> int:
        query = update.callback_query
        await query.answer()
       
        content = f"帳單: {context.user_data['bill']}"
        if not_enough:
            content += ", 存貨不足"

        reply_markup = InlineKeyboardMarkup(context.user_data["commodity_keyboard"])
        await query.edit_message_text(text=content, reply_markup=reply_markup)
        return self.COMMODITY
         
    async def stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: 
        query = update.callback_query
        await query.answer()
    
        context.user_data["item"] = query.data
        context.user_data["number"] = ""
    
        reply_markup = InlineKeyboardMarkup(context.user_data["number_keyboard"])
        await query.edit_message_text(text="輸入數量", reply_markup=reply_markup)
        return self.NUMBER

    async def enter_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if not context.user_data["number"]:
            if context.user_data["is_trade"]:
                return await self.add_buy(update, context)
            else:
                return await self.add_stock(update, context)
        
        query = update.callback_query
        await query.answer()

        item = context.user_data["item"]
        if context.user_data["is_trade"]:
            order_amount = int(context.user_data["number"])
            context.user_data["number"] = ""
            
            if item in context.user_data["stock"]:
                stock_amount = context.user_data["stock"][item]["amount"]
                
                if order_amount <= stock_amount:
                    context.user_data["order"][item] = order_amount
                    context.user_data["bill"] = self.get_order_value(context)
                    return await self.add_buy(update, context)

            return await self.add_buy(update, context, not_enough=True)
        
        else:
            context.user_data["stock"][item] = {"amount": int(context.user_data["number"])}
            context.user_data["number"] = ""
            return await self.add_stock(update, context)
    
    async def show(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        
        inventory_lst = [f"{k} {v['amount']}" for k, v in context.user_data["stock"].items()]
        content = "\n".join(inventory_lst) if inventory_lst else "Empty stock"
       
        return await self.stock_menu(update, context, content=content)
   
    async def coupon(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
       
        if query.data == "coupon":
            context.user_data["use_coupon"] = True
        elif query.data == "decoupon":
            context.user_data["use_coupon"] = False

        return await self.trade_menu(update, context)
   
    async def number(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
      
        if query.data == "<":
            context.user_data["number"] = context.user_data["number"][:-1]
        else:
            context.user_data["number"] += query.data
        
        reply_markup = InlineKeyboardMarkup(context.user_data["number_keyboard"])
        await query.edit_message_text(text=f": {context.user_data['number']}", reply_markup=reply_markup)
        return self.NUMBER

    def get_order_value(self, context) -> int:
        value = 0
        discount = 5 if context.user_data["use_coupon"] else 0
        for amt in context.user_data["order"].values():
            value += amt * (50 - discount) 

        return value

    def checkout(self, context) -> int:
        for item, amt in context.user_data["order"].items():
            context.user_data["stock"][item]["amount"] -= amt

        context.user_data["revenue"] += context.user_data["bill"]
        context.user_data["bill"] = 0
        context.user_data["order"] = {}

def main() -> None:
    payapaya = Backery("5820455690:AAEoNOvm-wcHj-RW3LwobzychdGXeG8MZf0")
    payapaya.start_to_work()

if __name__ == "__main__":
    main()
