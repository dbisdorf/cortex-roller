from django.shortcuts import render, redirect, reverse
from .models import Die, Message, Roll
from django.http import JsonResponse
import json
import random

#TODO any mechanism to cut down on accidental reassignment of the same room? like a history of room inactivity?

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
    #TODO is it confusing to sort dice by faces? especially after you step up or down?
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

# view functions

def index(request, room_name=None):
    if not room_name:
        return redirect(reverse('index') + get_random_words(3) + '/')

    result_dice_list = Die.objects.all()

    #TODO maybe no need to include the result dice list in the context

    context = {
            'result_dice_list': result_dice_list
    }
    return render(request, 'players/index.html', context)


def ajax(request, room_name):
    command = request.POST.get('command', None)
    param = request.POST.get('param', None)

    # TODO in theory I should throw an error for invalid commands
    # TODO why do some of my mouse clicks not given an immediate result?

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
                die.tag = 'T'
                die.selected = False
            elif die.tag == 'T':
                die.tag = 'X'
            die.save()

    if command == 'effectdice':
        dice_list = Die.objects.filter(room=room_name)
        for die in dice_list:
            if die.selected:
                die.tag = 'E'
                die.selected = False
            elif die.tag == 'E':
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

    response = {}

    message_list = Message.objects.filter(room=room_name).order_by('timestamp')
    message_text_list = [{'uuid':m.uuid, 'text':m.text} for m in message_list]
    response['message_list'] = message_text_list

    dice_list = Die.objects.filter(room=room_name).order_by('faces', 'timestamp')
    dice_text_list = [{'uuid':d.uuid, 'faces':d.faces, 'result':d.result, 'selected':d.selected, 'tag':d.tag} for d in dice_list]
    response['dice_list'] = dice_text_list

    roll_list = Roll.objects.filter(room=room_name).order_by('-timestamp')
    roll_text_list = [r.text for r in roll_list]
    response['roll_list'] = roll_text_list

    response['roll'] = evaluate_dice()

    return JsonResponse(response)

