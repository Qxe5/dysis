# dysis

Yu-Gi-Oh! Card Search Discord Bot

Dysis includes autocomplete for searches with paginated results for much improved accuracy

## Commands

| Command    | Description                              |
| -------    | -----------                              |
| `/search`  | Search for TCG / OCG / Skill cards       |
| `/arts`    | Search for all artworks of a card        |
| `/rulings` | Search for all rulings related to a card |
| `/servers` | Get the server count of Dysis            |

<img src='https://cdn.discordapp.com/attachments/936463189237977139/970711136980840558/search.gif' width=443>

## Common Options

Every command includes the following options:

* `card` - An autocompleting card name **(Required)**

* `mention` - A member you would like to share your search results with **(Optional)**

* `public` - The option of a ephemeral response to help with channel clogging **(Optional)**

## `/rulings` Options

* `question` - Sort results by keywords in the question **(Optional)**
* `qa` - Sort results by YGOrg Q&A ID **(Optional)**

[Add to Server](https://discord.com/api/oauth2/authorize?client_id=937841297669124137&permissions=0&scope=bot%20applications.commands)

<details>
<summary>Setup Your Own Instance</summary>

**Requires Python 3.10.x or later**

0. Create a Discord bot with
    * Scopes: `bot`, `applications.commands`
    * Permissions: `None`

1. Execute
```
% python -m pip install --requirement requirements.txt
% python bot.py
```

[Docker](https://hub.docker.com/r/dotbotio/dysis)
</details>

<details>
<summary>Credits</summary>

* **Liz** (Lead Designer)
* **Mac** (Lead Tester)
* **Sam** (Tester)
</details>
