# SO-EditMonitor
EditMonitor is a bot (written in Python 2.7) that monitors recent suggested edits on [Stack Overflow](http://stackoverflow.com) and posts an alert in a chatroom when it comes across an approved edit with 2 rejection votes. The bot uses [ChatExchange](https://github.com/Manishearth/ChatExchange) for the chat interaction.

EditMonitor uses the Stack Exchange API to get a list of the most recent edits. If you have an API key that you want to use, create a file ApiKey.txt and put the API key in there. The bot will use this if it exists.

Example chat post:

![Image of example chat post](https://i.imgur.com/qQDQ1wj.png)
