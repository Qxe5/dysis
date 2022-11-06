'''Score management'''
import shelve

async def record(user, correct):
    '''Update the users score based off whether they were correct and return it'''
    user = str(user)
    path = 'cache/scores'

    with shelve.open(path) as scores:
        if user not in scores:
            scores[user] = (1, 0) if correct else (0, 1)
        else:
            wins, losses = scores[user]
            scores[user] = (wins + 1, losses) if correct else (wins, losses + 1)

        return scores[user]
