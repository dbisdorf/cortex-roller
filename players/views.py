from django.shortcuts import render, redirect, reverse
from django.utils import timezone
from .models import Die, Message, Roll, Room
from django.http import JsonResponse
import json
import random
import datetime

WORDS = [
        'Attic',
        'Bauble',
        'Cavort',
        'Douse',
        'Expel',
        'Flinch',
        'Grant',
        'Heckle',
        'Import',
        'Jockey',
        'Karma',
        'Listen',
        'Maple',
        'Needy',
        'Often',
        'Penny',
        'Quite',
        'Rubric',
        'Salvo',
        'Teach',
        'Union',
        'Verse',
        'Waltz',
        'Xerox',
        'Yokel',
        'Zilch'
]

# utility functions

def get_random_words(num_words):
    all = []
    for count in range(num_words):
        all.append(random.choice(WORDS))
    return ''.join(all)

def evaluate_dice():
    total = 0
    effect = ''
    dice_list = Die.objects.order_by('faces', 'timestamp')
    for die in dice_list:
        if die.tag == 'T':
            total = total + die.result
        if die.tag == 'E':
            effect = effect + 'D' + str(die.faces) + ' '
    if not total:
        total = 'None'
    if not effect:
        effect = 'None'
    return 'Total: {0} - Effect: {1}'.format(total, effect)

def update_room_time(room_name):
    active_room = Room.objects.get(name=room_name)
    active_room.timestamp = timezone.now()
    active_room.save()

# view functions

def index(request, room_name=None):
    if not room_name:
        # purge old rooms
        purge_time = timezone.now() - datetime.timedelta(days=30)
        old_rooms = Room.objects.filter(timestamp__lt=purge_time)
        for old_room in old_rooms:
            Die.objects.filter(room=old_room.name).delete()
            Message.objects.filter(room=old_room.name).delete()
            Roll.objects.filter(room=old_room.name).delete()
            old_room.delete()

        # choose new room
        room_chosen = False
        while not room_chosen:
            new_room_name = get_random_words(3)
            existing_rooms = Room.objects.filter(name=new_room_name)
            if not existing_rooms:
                room_chosen = True

        new_room = Room(name=new_room_name)
        new_room.save()
        return redirect(reverse('index') + new_room_name + '/')

    result_dice_list = Die.objects.all()

    context = {
            'result_dice_list': result_dice_list
    }
    return render(request, 'players/index.html', context)


def ajax(request, room_name):
    command = request.POST.get('command', None)
    param = request.POST.get('param', None)

    if command == 'message':
        new_message_text = param

        if not new_message_text:
            new_message_text = '...'
        new_message = Message(room=room_name, text=new_message_text)
        new_message.save()

    if command == 'delmessage':
        Message.objects.filter(uuid=param).delete()

    if command == 'adddie':
        new_die = Die(room=room_name, faces=param)
        new_die.save()

    if command == 'roll':
        random.seed()
        dice_text_list = []
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            die.roll()
            die.tag = 'X'
            die.save()

    if command == 'delall':
        Die.objects.filter(room=room_name).delete()

    if command == 'deldice':
        Die.objects.filter(room=room_name, selected=True).delete()

    if command == 'totaldice':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.selected:
                if die.result > 1:
                    die.tag = 'T'
                die.selected = False
            elif die.tag == 'T':
                die.tag = 'X'
            die.save()

    if command == 'effectdice':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.selected:
                if die.result > 1:
                    die.tag = 'E'
                die.selected = False
            elif die.tag == 'E':
                die.tag = 'X'
            die.save()

    if command == 'totalbest':
        marked = 0
        dice_list = Die.objects.filter(room=room_name).order_by('-result')
        for die in dice_list:
            if die.result > 1 and marked < 2 and die.tag != 'E':
                die.tag = 'T'
                marked += 1
            elif die.tag == 'T':
                die.tag = 'X'
            die.save()

    if command == 'effectbest':
        marked = 0
        dice_list = Die.objects.filter(room=room_name).order_by('-faces')
        for die in dice_list:
            if die.result > 1 and marked < 1 and die.tag != 'T':
                die.tag = 'E'
                marked += 1
            elif die.tag == 'E':
                die.tag = 'X'
            die.save()

    if command == 'tagnone':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.tag != 'X':
                die.tag = 'X'
                die.save()

    if command == 'keep':
        new_roll = Roll(room=room_name, text=evaluate_dice())
        new_roll.save()

    if command == 'toggledie':
        die = Die.objects.get(uuid=param)
        die.selected = not die.selected
        die.save()

    if command == 'updice':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.selected and die.faces < 12:
                die.faces += 2
                die.result = 0
                die.selected = False
                die.save()

    if command == 'downdice':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.selected and die.faces > 4:
                die.faces -= 2
                die.result = 0
                die.selected = False
                die.save()

    if command == 'clearhistory':
        Roll.objects.filter(room=room_name).delete()

    update_room_time(room_name)

    response = {}

    message_list = Message.objects.filter(room=room_name).order_by('timestamp')
    message_text_list = [{'uuid':m.uuid, 'text':m.text} for m in message_list]
    response['message_list'] = message_text_list

    dice_list = Die.objects.filter(room=room_name).order_by('faces', 'timestamp')
    dice_text_list = [{'uuid':d.uuid, 'faces':d.faces, 'result':d.result, 'selected':d.selected, 'tag':d.tag, 'timestamp':d.timestamp} for d in dice_list]
    response['dice_list'] = dice_text_list

    roll_list = Roll.objects.filter(room=room_name).order_by('-timestamp')
    roll_text_list = [r.text for r in roll_list]
    response['roll_list'] = roll_text_list

    response['roll'] = evaluate_dice()

    return JsonResponse(response)

