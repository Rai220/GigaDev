from tempfile import TemporaryDirectory

from langchain import hub
from langchain.agents import (AgentExecutor, create_openai_tools_agent)
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools import ShellTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI



llm = ChatOpenAI(temperature=1, model="gpt-4")

shell_tool = ShellTool(ask_human_input=False)

shell_tool.description = shell_tool.description + f"args {shell_tool.args}".replace(
    "{", "{{"
).replace("}", "}}")

# We'll make a temporary directory to avoid clutter
working_directory = TemporaryDirectory()
toolkit = FileManagementToolkit()

tools = [shell_tool]
tools.extend(toolkit.get_tools())

# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-tools-agent")


agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

# Load scripts/README.md to string
with open("scripts/README.md", "r", encoding="utf-8") as file:
    readme = file.read()

postfix = "\nЕсли в коллекции готовых скриптов есть нужный скрипт, то используй в первую очередь его. Если ты успешно выполнил задачу, то обязательно напиши набор команд, который был использован для этого, затем напиши КОНЕЦ."
prompt.messages[
    0
].prompt.template = f"""Ты - профессональный разработчик, который решает задачи.
Ты работаешь с консолью в безопасной среде с операционной системой MacOS, 
поэтому можешь выполнять любые команды и модифицировать файлы, 
для этого у тебя есть набор инструментов.
Также ты пишешь полезные скрипты, которые можешь использовать в дальнейшем. Несколько скриптов ты уже написал.

В твоей директории лежит файл scripts/README.md, в нем записано, какие скрипты ты уже написал и какие задачи они решают.
Вот содержимое файла:
```
{readme}
```

Обязательно используй эти команды там, где это возможно, поскольку ты их уже проверил!

Прежде чем сделать что-либо ты сначала изучаешь структуру проекта, затем выполняешь команды, чтобы решить задачу.
Не торопись, рассуждай, планируй, действуй шаг за шагом, не пытайся сразу же решить задачу с помощью одной команды.
Если задачу не получилось решить, то продолжай делать попытки, решай её разными способами, изучай окружение.
Ты должен именно выполнить задачу, используя инструменты, а не написать инструкцию по её выполнению.
Только когда ты выполнил команду напиши КОНЕЦ. Если задача решена и не 
предполагает продолжения или требует действий от пользователя, пиши КОНЕЦ.
Перед этим ОБЯЗАТЕЛЬНО!!! напиши пользователю bash-команды, которые ты выполнил для решения задачи.
Ты можешь запрашивать уточнения у пользователя, если тебе что-то непонятно или в процессе решения задачи потребовались дополнительные данные. """ + postfix

history = []

counter = 0
while True:
    command = input("Введите новую команду: ") + postfix
    
    global_task = command

    for i in range(0, 5):
        counter += 1
        res = agent_executor.invoke({"input": command, "chat_history": history})

        output = res["output"]
        history.append(HumanMessage(content=command))
        history.append(AIMessage(content=output))
        print(f"Bot: {res['output']}")
        if "КОНЕЦ" in output.upper():
            break
        else:
            command = f"""Продолжай решать задачу, которая звучала так: '{command}.
Если задача решена и не предполагает продолжения или требует действий от пользователя, пиши КОНЕЦ.
Не пиши КОНЕЦ, если задача решена не до конца. Ты продолжишь её выполнение после следующего запроса от пользователя.'"""


    # Эта часть не идёт в историю
    final_command = """Если задача была успешно решена с помощью команды консоли, 
    и это решение можно использовать в будущем, 
    то создай bash-скрипт в директории scripts.
    Придумай название для файла скрипта, чтобы ты точно смог понять, что он делает в будуем.
    Сделай скрипт запускаемым с помощью chmode +x.
    Для создания скрипта используй доступ к консоли, например через cat > file.sh
    Добавь название скрипта и его функции в README файл.
    Если решенная задача не требует создания скрипта или ты воспользовался готовым скриптом - просто верни OK.
    Не создавай одинаковые скрипты!!! Не создавай бессмысленных или слишком простых скриптов, вместо этого просто пиши ОК, тогда скрипт не будет создан."""
    res = agent_executor.invoke({"input": final_command, "chat_history": history})

