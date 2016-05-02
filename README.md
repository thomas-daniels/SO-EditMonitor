# EditMonitor
EditMonitor is a bot (written in Python 2.7) that monitors recent suggested edits on [Stack Overflow](http://stackoverflow.com) and posts an alert in a chatroom when it comes across a suspicious suggested edit (detected as spam, approved with 2 rejection votes ...). The bot uses [ChatExchange](https://github.com/Manishearth/ChatExchange) for the chat interaction.

EditMonitor uses the Stack Exchange API to get a list of the most recent edits. If you have an API key that you want to use, create a file ApiKey.txt and put the API key in there. The bot will use this if it exists.

Example chat post:

![Image of example chat post](https://i.imgur.com/qQDQ1wj.png)

EditMonitor is licensed under the [CodeProject Open License v1.02](http://www.codeproject.com/info/cpol10.aspx). You can find a copy of this license in LICENSE.htm.
