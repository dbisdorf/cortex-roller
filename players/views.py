from django.shortcuts import render, redirect, reverse
from django.utils import timezone
from .models import Die, Message, Roll, Room, Tally
from django.http import JsonResponse, HttpResponse
#from PIL import Image, ImageDraw, ImageFont
import io
import json
import random
import datetime

WORDS = [
        'Adapt', 'Attic', 'Alarm',
        'Badge', 'Bauble', 'Breath',
        'Cavort', 'Clean', 'Craft',
        'Dally', 'Defer', 'Douse',
        'Eager', 'Edify', 'Expel',
        'Faint', 'Flinch', 'Forgot',
        'Gander', 'Ghost', 'Grant',
        'Habit', 'Heckle', 'Hound',
        'Ideal', 'Import', 'Issue',
        'Jewel', 'Jockey', 'Judge',
        'Karma', 'Kiosk', 'Knock',
        'Lagoon', 'Listen', 'Logic',
        'Maple', 'Medal', 'Mirth',
        'Nature', 'Needy', 'North',
        'Octave', 'Often', 'Optic',
        'Packet', 'Penny', 'Pledge',
        'Quack', 'Quest', 'Quite',
        'Radio', 'Remedy', 'Rubric',
        'Salvo', 'Scold', 'Sharp',
        'Tacit', 'Teach', 'Today',
        'Ultra', 'Union', 'Urban',
        'Vague', 'Verse', 'Vigil',
        'Waist', 'Waltz', 'Whirl',
        'Xenon', 'Xerox',
        'Yield', 'Yokel', 'Youth',
        'Zebra', 'Zilch', 'Zinc'
]

DICE = [4, 6, 8, 10, 12]

ROLL_FETCH_LIMIT = 10
ROOM_PURGE_PERIOD = 15
ROLL_PURGE_PERIOD = 180
RANDOM_REPORT_PERIOD = 14

# utility functions

def roll(die):
    die.result = random.SystemRandom().randint(1, die.faces)
    today = datetime.date.today()
    tally = None
    try:
        tally = Tally.objects.get(date=today, faces=die.faces, result=die.result)
    except Tally.DoesNotExist:
        tally = Tally(date=today, faces=die.faces, result=die.result)
    tally.tally += 1
    tally.save()

def get_random_words(num_words):
    all = []
    for count in range(num_words):
        all.append(random.SystemRandom().choice(WORDS))
    return ''.join(all)

def get_dice_from_roll(roll_uuid):
    return Die.objects.filter(owner=roll_uuid)

def evaluate_dice(dice_list):
    total = 0
    effect = ''
    any_rolled = False
    for die in dice_list:
        if die.result > 0:
            any_rolled = True
        if die.tag == 'T':
            total = total + die.result
        if die.tag == 'E':
            effect = effect + 'D' + str(die.faces) + ' '
    if not total:
        total = 'None'
    if not effect:
        if any_rolled:
            effect = 'D4'
        else:
            effect = 'None'
    return 'Total: {0} - Effect: {1}'.format(total, effect)

def latest_update(record_list):
    if not record_list:
        return ''
    latest_record = max(record_list, key=lambda r: r.updated)
    return latest_record.updated

# view functions

def index(request, room_name=None):
    if not room_name:
        # purge old rooms
        purge_time = timezone.now() - datetime.timedelta(days=ROOM_PURGE_PERIOD)
        old_rooms = Room.objects.filter(timestamp__lt=purge_time)
        for old_room in old_rooms:
            Die.objects.filter(owner=old_room.uuid).delete()
            Message.objects.filter(owner=old_room.uuid).delete()
            old_room.delete()

        # purge old rolls
        purge_time = timezone.now() - datetime.timedelta(days=ROLL_PURGE_PERIOD)
        old_rolls = Roll.objects.filter(updated__lt=purge_time)
        for old_roll in old_rolls:
            Die.objects.filter(owner=old_roll.uuid).delete()
            old_roll.delete()

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

    return render(request, 'players/index.html', {})

def ajax(request, room_name):
    command = request.POST.get('command', None)
    param = request.POST.get('param', None)
    room = Room.objects.get(name=room_name)

    valid_command = True

    if command == 'message':
        new_message_text = param

        if not new_message_text:
            new_message_text = '...'
        new_message = Message(owner=room.uuid, text=new_message_text)
        new_message.save()

    elif command == 'delmessage':
        Message.objects.filter(uuid=param).delete()

    elif command == 'adddie':
        new_die = Die(owner=room.uuid, faces=param)
        new_die.save()

    elif command == 'rollall':
        dice_text_list = []
        dice_list = Die.objects.filter(owner=room.uuid)
        for die in dice_list:
            roll(die)
            die.tag = 'X'
            die.updated = timezone.now()
            die.save()

    elif command == 'rolldice':
        selected_ids = param.split(',')
        dice_text_list = []
        dice_list = Die.objects.filter(owner=room.uuid, uuid__in=selected_ids)
        for die in dice_list:
            roll(die)
            die.tag = 'X'
            die.updated = timezone.now()
            die.save()

    elif command == 'delall':
        Die.objects.filter(owner=room.uuid).delete()

    elif command == 'deldice':
        selected_ids = param.split(',')
        Die.objects.filter(owner=room.uuid, uuid__in=selected_ids).delete()

    elif command == 'totaldice':
        selected_ids = param.split(',')
        dice_list = Die.objects.filter(owner=room.uuid)
        for die in dice_list:
            if str(die.uuid) in selected_ids:
                print('in selection');
                if die.result > 1:
                    die.tag = 'T'
                die.updated = timezone.now()
            elif die.tag == 'T':
                die.tag = 'X'
                die.updated = timezone.now()
            die.save()

    elif command == 'effectdice':
        selected_ids = param.split(',')
        dice_list = Die.objects.filter(owner=room.uuid)
        for die in dice_list:
            if str(die.uuid) in selected_ids:
                if die.result > 1:
                    die.tag = 'E'
                die.updated = timezone.now()
            elif die.tag == 'E':
                die.tag = 'X'
                die.updated = timezone.now()
            die.save()

    elif command == 'totalbest':
        marked = 0
        dice_list = Die.objects.filter(owner=room.uuid).order_by('-result', 'faces')
        for die in dice_list:
            if die.result > 1 and marked < 2 and die.tag != 'E':
                die.tag = 'T'
                die.updated = timezone.now()
                marked += 1
            elif die.tag == 'T':
                die.tag = 'X'
                die.updated = timezone.now()
            die.save()

    elif command == 'effectbest':
        marked = 0
        dice_list = Die.objects.filter(owner=room.uuid).order_by('-faces', 'result')
        for die in dice_list:
            if die.result > 1 and marked < 1 and die.tag != 'T':
                die.tag = 'E'
                die.updated = timezone.now()
                marked += 1
            elif die.tag == 'E':
                die.tag = 'X'
                die.updated = timezone.now()
            die.save()

    elif command == 'tagnone':
        dice_list = Die.objects.filter(owner=room.uuid)
        for die in dice_list:
            if die.tag != 'X':
                die.tag = 'X'
                die.updated = timezone.now()
                die.save()

    elif command == 'keep':
        new_roll = Roll(owner=room.uuid)
        new_roll.save()
        dice_list = Die.objects.filter(owner=room.uuid, tag__in='TE')
        for die in dice_list:
            copy_die = Die(faces=die.faces, result=die.result, tag=die.tag, owner=new_roll.uuid)
            copy_die.save()

    elif command == 'updice':
        selected_ids = param.split(',')
        dice_list = Die.objects.filter(owner=room.uuid, uuid__in=selected_ids)
        for die in dice_list:
            if die.faces < 12:
                die.faces += 2
                die.result = 0
                die.updated = timezone.now()
                die.save()

    elif command == 'downdice':
        selected_ids = param.split(',')
        dice_list = Die.objects.filter(owner=room.uuid, uuid__in=selected_ids)
        for die in dice_list:
            if die.faces > 4:
                die.faces -= 2
                die.result = 0
                die.updated = timezone.now()
                die.save()

    elif command == 'clearhistory':
        Roll.objects.filter(owner=room.uuid).delete()

    elif command != 'poll':
        valid_command = False

    response = {}

    if valid_command:
        if command != 'poll':
            # update room timestamp
            room.timestamp = timezone.now()
            room.save()

        message_list = Message.objects.filter(owner=room.uuid).order_by('created')
        message_text_list = [{'uuid':m.uuid, 'text':m.text} for m in message_list]
        response['message_list'] = message_text_list
        response['message_update'] = latest_update(message_list)

        dice_list = Die.objects.filter(owner=room.uuid).order_by('faces')
        dice_text_list = [{'uuid':d.uuid, 'faces':d.faces, 'result':d.result, 'tag':d.tag, 'timestamp':d.created} for d in dice_list]
        response['dice_list'] = dice_text_list
        response['dice_update'] = latest_update(dice_list)

        roll_list = Roll.objects.filter(owner=room.uuid).order_by('-created')[:ROLL_FETCH_LIMIT]
        roll_text_list = [{'uuid':r.uuid, 'text':evaluate_dice(Die.objects.filter(owner=r.uuid).order_by('faces'))} for r in roll_list]
        response['roll_list'] = roll_text_list
        response['roll_update'] = latest_update(roll_list)

        response['roll'] = evaluate_dice(dice_list)
    else:
        response['error'] = 'Invalid command'

    return JsonResponse(response)

def rolls(request, roll_id):
    roll = Roll.objects.get(uuid=roll_id)
    dice = Die.objects.filter(owner=roll_id).order_by('-tag', 'faces')

    '''
    image = Image.new('RGB', (640, 160), (255, 255, 255))
    image.paste(d4, (0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), roll.text, fill=(0, 0, 0), font=font)

    response = HttpResponse(content_type='image/jpeg')
    image.save(response, 'JPEG')
    return response
    '''

    context = {'timestamp': roll.updated, 'overall': evaluate_dice(dice), 'dice':dice}
    return render(request, 'players/roll.html', context)

def random_report(request):
    activity = None
    recent_room = Room.objects.order_by('-timestamp').first()
    if recent_room:
        activity = recent_room.timestamp
    matrix = [[0] * 13 for die in range(len(DICE))]
    report_start = datetime.date.today() - datetime.timedelta(days=RANDOM_REPORT_PERIOD)
    tallies = Tally.objects.filter(date__gt=report_start)
    total_rolls = 0
    for tally in tallies:
        index = DICE.index(tally.faces)
        matrix[index][0] += tally.tally
        matrix[index][tally.result] += tally.tally
        total_rolls += tally.tally
    dice = []
    index = 0
    for column in matrix:
        die = {'faces':DICE[index], 'rolls':column[0], 'tallies':[]}
        for result in range(1, DICE[index] + 1):
            tally = {'result': result, 'tally':column[result], 'percent':int(round(column[result]/column[0], 2)*100)}
            die['tallies'].append(tally)
        dice.append(die)
        index += 1
    context = {'period': RANDOM_REPORT_PERIOD, 'total_rolls': total_rolls, 'activity': activity, 'dice':dice}
    return render(request, 'players/random.html', context)
