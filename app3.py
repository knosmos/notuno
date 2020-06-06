from flask import Flask, flash, request, redirect, url_for, render_template, jsonify, make_response
import copy, random, pickle

app = Flask(__name__)

class User():
    def __init__(self, name):
        self.team = False
        self.cards = generateCards(7) # TODO change to 7
        self.id = getRandomId()
        try: self.name = unicode(name,'utf-8')
        except: self.name = name

waiting_users = []
playing_users = []
top_cards = []
win_data = []
turn_data = []
used_ids = []

def getData():
    # get data from pickle
    global waiting_users, playing_users, top_cards, win_data, turn_data, used_ids
    try:
        with open('data.pickle','rb') as p:
            waiting_users, playing_users, top_cards, win_data, turn_data, used_ids = pickle.load(p)
    except:
        print('File does not exist')

def writeData():
    global waiting_users, playing_users, top_cards, win_data, turn_data, used_ids
    with open('data.pickle','wb') as p:
        data = [waiting_users, playing_users, top_cards, win_data, turn_data, used_ids]
        pickle.dump(data,p,3)

def getRandomId():
    global used_ids
    getData()
    used_set = set(used_ids)
    new_id = ''
    while new_id in used_set or new_id == '':
        for i in range(3):
            new_id += random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_') # Base 64
    used_ids.append(new_id)
    writeData()
    return new_id

def getRandomCard():
    color = random.choice(['blue','green','red','yellow'])
    num = random.randint(0,9)
    return [color,num]

def generateCards(num):
    cards = []
    for i in range(num):
        cards.append(getRandomCard())
    return cards

@app.route('/login',methods=['GET','POST'])
def login():
    getData()
    if request.method == 'POST':
        user = User(request.form['name'])
        r = make_response(redirect('/wait'))
        r.set_cookie('id',user.id)
        waiting_users.append(user)
        writeData()
        return r
    return render_template('start.html')

@app.route('/_refreshusers')
def refreshUsers():
    global waiting_users
    getData()
    print([str(i.name) for i in waiting_users])
    return jsonify([str(i.name) for i in waiting_users])

@app.route('/_started')
def getStarted():
    global waiting_users
    getData()
    if len(waiting_users) == 0:
        return 'yes'
    return 'no'

@app.route('/_currentcard')
def currentcard():
    global top_cards
    getData()
    g = int(request.args.get('group'))
    return jsonify(top_cards[g])

@app.route('/_getgroupusers')
def getGroupUsers():
    global playing_users
    getData()
    g = int(request.args.get('group'))
    print([str(x.name) for x in playing_users[g]])
    return jsonify([str(x.name) for x in playing_users[g]])

@app.route('/_playcard')
def playCard():
    global top_cards, playing_users, win_data
    getData()
    color = str(request.args.get('color'))
    num = int(request.args.get('num'))
    group = int(request.args.get('group'))
    id = str(request.args.get('id'))
    moveNum = int(request.args.get('move'))
    if top_cards[group][1] == num or (top_cards[group][0] == color and moveNum == 0):
        top_cards[group] = [color,num]
        for i in playing_users[group]:
            if i.id == id:
                current_user = i
        current_user.cards.remove([color,num])
        if len(current_user.cards) == 0:
            win_data[group] = current_user.name
        writeData()
        return jsonify(current_user.cards)
    return 'invalid'

@app.route('/_usercards')
def userCards():
    global playing_users
    getData()
    group = int(request.args.get('group'))
    id = str(request.args.get('id'))
    for i in playing_users[group]:
        if i.id == id:
            current_user = i
    return jsonify(current_user.cards)

@app.route('/_addcard')
def addCard():
    global playing_users
    getData()
    group = int(request.args.get('group'))
    id = str(request.args.get('id'))
    for i in playing_users[group]:
        if i.id == id:
            current_user = i
    current_user.cards.append(getRandomCard())
    writeData()
    return 'done'

@app.route('/_advanceturn')
def advanceTurn():
    global turn_data, playing_users
    getData()
    group = int(request.args.get('group'))
    turn_data[group] += 1
    if turn_data[group] >= len(playing_users[group]):
        turn_data[group] = 0
    print(turn_data[group])
    writeData()
    return 'done'

@app.route('/_whoseturnisit')
def whoseturnisit():
    global turn_data
    getData()
    return str(turn_data[int(request.args.get('group'))])

@app.route('/_didsomeonewin')
def didSomeoneWin():
    global win_data
    getData()
    group = int(request.args.get('group'))
    if win_data[group] == False:
        return 'nope'
    return 'yes'

@app.route('/end',methods = ['GET','POST'])
def end():
    global playing_users, win_data
    getData()
    for group in range(len(playing_users)):
        for user in playing_users[group]:
            if user.id == request.cookies.get('id'):
                current_user = user
                user_group = group
                break
    if request.method == 'POST':
        current_user.cards = generateCards(7)
        waiting_users.append(current_user)
        playing_users[user_group].remove(current_user)
        writeData()
        return redirect('/wait')
    id = request.cookies.get('id')
    if win_data[user_group] == False:
        return redirect('/login')
    return render_template('end.html',winner=win_data[user_group])

@app.route('/wait',methods=['GET','POST'])
def wait():
    global waiting_users
    getData()
    if request.method == 'POST':
        playing_users.append(copy.deepcopy(waiting_users))
        waiting_users = []
        top_cards.append(getRandomCard())
        win_data.append(False)
        turn_data.append(0)
        writeData()
    return render_template('wait.html')

@app.route('/')
def main():
    global playing_users
    getData()
    if not request.cookies.get('id'):
        return redirect('/login')
    current_user = ''
    for group in range(len(playing_users)):
        for user in playing_users[group]:
            if user.id == request.cookies.get('id'):
                current_user = user
                user_group = group
                break
    if current_user == '':
        return redirect('/login')
    return render_template('main.html',name=current_user.name,group=user_group,id=current_user.id)

if __name__ == '__main__':
    app.run('0.0.0.0')