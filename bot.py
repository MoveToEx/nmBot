import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotAdapter
from nonebot.adapters.console import Adapter as ConsoleAdapter  # 避免重复命名

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OneBotAdapter)

# nonebot.load_builtin_plugins("echo")
# nonebot.load_plugin("thirdparty_plugin")  # 第三方插件
nonebot.load_plugins("nmbot/plugins")

if __name__ == "__main__":
    nonebot.run()