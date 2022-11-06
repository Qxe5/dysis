'''Score management'''
import shelve

async def record(user, correct):
    '''Update the users score based off whether they were correct and return it'''
    user = str(user)
    path = 'cache/scores'

    with shelve.open(path) as scores:
        if score := scores.setdefault(user, (1, 0) if correct else (0, 1)):
            wins, losses = score
            scores[user] = (wins + 1, losses) if correct else (wins, losses + 1)

        return scores[user]
