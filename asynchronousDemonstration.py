import pyNN.spiNNaker as sim
import threading
from time import sleep
from pykeyboard import PyKeyboard
import cv2
import numpy as np
import pyautogui
from datetime import datetime
from random import randint
import sys

sim.setup(timestep=1.0)
sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

numberOfSteps = 12
numberOfActions = 4

stateSpikeInjector = sim.Population(numberOfSteps * numberOfActions, sim.external_devices.SpikeInjector(), label="stateSpikeInjector")
actorSpikeInjector = sim.Population(numberOfSteps * numberOfActions, sim.external_devices.SpikeInjector(), label="actorSpikeInjector")
statePopulation = sim.Population(numberOfSteps * numberOfActions, sim.IF_curr_exp(tau_syn_E=100, tau_refrac=50), label="statePopulation")
actorPopulation = sim.Population(numberOfSteps * numberOfActions, sim.IF_curr_exp(tau_syn_E=25, tau_refrac=100), label="actorPopulation")
firstSpikeTrigger = sim.Population(numberOfSteps, sim.external_devices.SpikeInjector(), label="firstSpikeTrigger")

sim.external_devices.activate_live_output_for(statePopulation, database_notify_host="localhost", database_notify_port_num=19996)
sim.external_devices.activate_live_output_for(stateSpikeInjector, database_notify_host="localhost", database_notify_port_num=19998)
sim.external_devices.activate_live_output_for(actorPopulation, database_notify_host="localhost", database_notify_port_num=20000)
sim.external_devices.activate_live_output_for(actorSpikeInjector, database_notify_host="localhost", database_notify_port_num=20002)
sim.external_devices.activate_live_output_for(firstSpikeTrigger, database_notify_host="localhost", database_notify_port_num=20004)

timing_rule = sim.SpikePairRule(tau_plus=50.0, tau_minus=50.0,
                                A_plus=0.001, A_minus=0.001)
weight_rule = sim.AdditiveWeightDependence(w_max=5.0, w_min=-5.0)
stdp_model = sim.STDPMechanism(timing_dependence=timing_rule,
                               weight_dependence=weight_rule,
                               weight=2, delay=1)

stdp_projection = sim.Projection(statePopulation, actorPopulation, sim.OneToOneConnector(),
                                 synapse_type=stdp_model)

state_projection = sim.Projection(stateSpikeInjector, statePopulation, sim.OneToOneConnector(),
                                  synapse_type=sim.StaticSynapse(weight=5, delay=2))

actorProjection = sim.Projection(actorSpikeInjector, actorPopulation, sim.OneToOneConnector(),
                                 synapse_type=sim.StaticSynapse(weight=5, delay=0))

connectionList = []

for step in range(numberOfSteps-1):
    for action in range(numberOfActions):
        connectionList.append((action, action + numberOfActions))

moves_projection = sim.Projection(actorPopulation, actorPopulation, sim.FromListConnector(connectionList),
                                  synapse_type=sim.StaticSynapse(weight=5, delay=2))

connectionList = []

currentMove = 0
for step in range(numberOfSteps):
    for action in range(numberOfActions):
        connectionList.append((step, currentMove))
        currentMove += 1

first_spike_trigger_projection = sim.Projection(firstSpikeTrigger, statePopulation, sim.FromListConnector(connectionList),
                                                synapse_type=sim.StaticSynapse(weight=5, delay=2))

statePopulation.record(["spikes", "v"])
actorPopulation.record(["spikes", "v"])

k = PyKeyboard()

step = 1
log = []
nextAction = 0

prevXOffset = 0
prevYOffset = 0

didExplore = False
exploring = False


def execute_commands():
    global step, nextAction, prevXOffset, prevYOffset, exploring, didExplore, actionsBuffer, logger, log, numberOfActions
    actionsArray = []
    try:
        print 'Executing commands for step: ' + str(step)
        logger = 'step ' + str(step) + ': '
        for index in range(len(actionsBuffer)):
            actionsArray.append(actionsBuffer[index])
        commands = list(set(actionsArray))
        commands = [x for x in commands if x != -1]
        print 'Commands: \n' + str(commands)
        commands.sort()
        for neuron_id in commands:
            neuron_id %= numberOfActions
            if str(neuron_id) is '0':
                sleep(0.15)
                logger += ' went right, '
                k.press_key(k.right_key)
                sleep(0.5)
                k.release_key(k.right_key)
            if str(neuron_id) is '1':
                sleep(0.15)
                logger += ' went left, '
                k.press_key(k.left_key)
                sleep(0.5)
                k.release_key(k.left_key)
            if str(neuron_id) is '2':
                sleep(0.15)
                logger += ' jumped right, '
                k.press_key(k.space)
                k.press_key(k.right_key)
                sleep(0.5)
                k.release_key(k.space)
                k.release_key(k.right_key)
            if str(neuron_id) is '3':
                sleep(0.15)
                logger += ' jumped left, '
                k.press_key(k.space)
                k.press_key(k.left_key)
                sleep(0.5)
                k.release_key(k.space)
                k.release_key(k.left_key)
        sleep(0.5)


        # Figure out next action based on current state
        print 'For the next action in step ' + str(step + 1)
        image = pyautogui.screenshot(region=(0, 250, 1250, 700))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imwrite("screenCapture" + str(step) + ".png", image)
        meatboy_image = cv2.imread('meatboy.png')
        meatgirl_image = cv2.imread('meatgirl.png')
        large_image = cv2.imread("screenCapture" + str(step) + ".png")
        method = cv2.TM_SQDIFF_NORMED
        result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                                   large_image.astype(np.float32), method)
        result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                    large_image.astype(np.float32), method)
        mn, _, mnLoc, _ = cv2.minMaxLoc(result)
        mn2, _, mnLoc2, _ = cv2.minMaxLoc(result2)
        MPx, MPy = mnLoc
        MPx2, MPy2 = mnLoc2

        xOffset = MPx2 - MPx
        yOffset = MPy2 - MPy

        image = pyautogui.screenshot(region=(0, 250, 1250, 700))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imwrite("screenCapture" + str(step) + ".png", image)
        meatboy_image = cv2.imread('meatboy.png')
        meatgirl_image = cv2.imread('meatgirl.png')
        large_image = cv2.imread("screenCapture" + str(step) + ".png")
        method = cv2.TM_SQDIFF_NORMED
        result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                                   large_image.astype(np.float32), method)
        result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                    large_image.astype(np.float32), method)
        mn1, _, mnLoc, _ = cv2.minMaxLoc(result)
        mn21, _, mnLoc2, _ = cv2.minMaxLoc(result2)
        MPx, MPy = mnLoc
        MPx2, MPy2 = mnLoc2

        xOffset1 = MPx2 - MPx
        yOffset1 = MPy2 - MPy

        while abs(xOffset - xOffset1) > 5 and abs(yOffset - yOffset1) > 5:
            xOffset = xOffset1
            yOffset = yOffset1
            image = pyautogui.screenshot(region=(0, 250, 1250, 700))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            cv2.imwrite("screenCapture" + str(step) + ".png", image)
            meatboy_image = cv2.imread('meatboy.png')
            meatgirl_image = cv2.imread('meatgirl.png')
            large_image = cv2.imread("screenCapture" + str(step) + ".png")
            method = cv2.TM_SQDIFF_NORMED
            result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                                       large_image.astype(np.float32), method)
            result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                        large_image.astype(np.float32), method)
            mn1, _, mnLoc, _ = cv2.minMaxLoc(result)
            mn21, _, mnLoc2, _ = cv2.minMaxLoc(result2)
            MPx, MPy = mnLoc
            MPx2, MPy2 = mnLoc2
        print '=============================='
        print 'xOffset: ' + str(xOffset)
        print 'yOffset: ' + str(yOffset)

        # if very close to the goal just go directly to it
        if abs(xOffset) < 300 and abs(yOffset) < 20:
            print 'We\'re close to the goal'
            # too much to the left
            if xOffset > 0:
                logger += ' went right, '
                time = datetime.time(datetime.now())
                k.press_key(k.right_key)
                sleep(1)
                time = datetime.time(datetime.now())
            # too much to the right
            else:
                logger += ' went left, '
                time = datetime.time(datetime.now())
                k.press_key(k.left_key)
                sleep(1)
                time = datetime.time(datetime.now())
                k.release_key(k.left_key)
            logger += ' won the game!'
            log.append(logger)
            for logger in log:
                    print logger
            sys.exit()


        trows, tcols = meatboy_image.shape[:2]
        trows2, tcols2 = meatgirl_image.shape[:2]

        cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows),
                      (0, 255, 0), 2)
        cv2.rectangle(large_image, (MPx2, MPy2),
                      (MPx2 + tcols2, MPy2 + trows2), (0, 255, 0), 2)
        cv2.imwrite("screenCapture" + str(step) + ".png", large_image)
        # too low
        if yOffset < 0:
            # too much to the left
            if xOffset > 0:
                print 'jump right'
                nextAction = 2
            # too much to the right
            else:
                print 'jump left'
                nextAction = 3
        else:
            # too much to the left
            if xOffset > 0:
                print 'go right'
                nextAction = 0
            # too much to the right
            else:
                print 'go left'
                nextAction = 1
        if not exploring:
            nextAction = step * 4 + nextAction
        else:
            print 'Exploring'
            print 'Action suggested by environment ' + str(nextAction)
            chosenAction = randint(0, 3)
            # while the explored action belongs to the same class as the action suggested by the environment
            # try to pick another action to explore
            while chosenAction % 2 is nextAction % 2:
                chosenAction = randint(0, 3)
            nextAction = chosenAction
            nextAction = step * 4 + nextAction
        print 'Next action: ' + str(nextAction)
        print 'Checking progress'
        if step is 1:
            prevXOffset = abs(xOffset)
            prevYOffset = abs(yOffset)



        # if progress has been made in any direction
        elif abs(xOffset) + 5 < prevXOffset or abs(yOffset) + 5 < prevYOffset:
            exploring = False
            logger += ' better than previous step'
            print 'better than previous step'
            # reward
            for index in range(0, len(commands)):
                reward = numberOfSteps - step + index + 1
                for i in range(0, reward):
                    send_spike('stateSpikeInjector', pre_synaptic_spikes_connection, commands[index])
                reward -= 1
                prevXOffset = abs(xOffset)
                prevYOffset = abs(yOffset)
        else:
            if not didExplore:
                exploring = True
            logger += ' worse than previous step'
            print 'worse than previous step'
            # punishment
            for index in range(0, len(commands)):
                punishment = numberOfSteps - step + index + 1
                for i in range(0, punishment):
                    # fire post synaptic neuron
                    send_spike('actorSpikeInjector', post_synaptic_spikes_connection, commands[index])
                    # then fire pre-synaptic neuron
                    send_spike('stateSpikeInjector', pre_synaptic_spikes_connection, commands[index])

                punishment -= 1
            prevXOffset = abs(xOffset)
            prevYOffset = abs(yOffset)
        didExplore = exploring
        step += 1
        log.append(logger)
    except RuntimeError:
        pass


firstSpike = True
decodingActions = False
currentStep = 0


def spike_receiver(label, time, neuron_ids):
    global firstSpike, currentStep, actionsBuffer, decodingActions
    try:
        for neuron_id in neuron_ids:
            if decodingActions and firstSpike:
                'We are checking the weights'
                actionsBuffer[currentStep] = neuron_id
                print 'Set best action of step ' + str(currentStep) + ' to be ' + str(actionsBuffer[currentStep])
                firstSpike = False
                break
    except RuntimeError:
        pass



actor_spikes_connection = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=["actorPopulation"], local_port=20000, send_labels=None)

pre_synaptic_spikes_connection = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=None, local_port=19998, send_labels=['stateSpikeInjector'])

post_synaptic_spikes_connection = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=None, local_port=20002, send_labels=['actorSpikeInjector'])

first_spike_trigger_connection = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=None, local_port=20004, send_labels=['firstSpikeTrigger'])

actor_spikes_connection.add_receive_callback("actorPopulation", spike_receiver)


def send_spike(label, sender, index):
    sender.send_spike(label, index, send_full_keys=True)


weightRight = []
weightLeft = []
weightJumpRight = []
weightJumpLeft = []


def press_key(key):
    k.press_key(key)
    sleep(0.2)
    k.release_key(key)
    sleep(0.2)


weights = []


class Step:
    weightPlotRight = []
    weightPlotLeft = []
    weightPlotJumpRight = []
    weightPlotJumpLeft = []


listOfStepObjects = [Step() for i in range(numberOfSteps)]


def restart_game():
    print 'Restarting game'
    press_key(k.escape_key)
    press_key(k.down_key)
    press_key(k.enter_key)
    sleep(0.2)
    press_key(k.right_key)
    press_key(k.enter_key)
    sleep(0.5)

    press_key(k.escape_key)
    press_key(k.down_key)
    press_key(k.enter_key)
    sleep(0.2)
    press_key(k.left_key)
    press_key(k.enter_key)


def get_first_action():
    global nextAction, step
    sleep(1)
    restart_game()
    sleep(1)
    image = pyautogui.screenshot(region=(0, 250, 1250, 700))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite("screenCapture0.png", image)
    meatboy_image = cv2.imread('meatboy.png')
    meatgirl_image = cv2.imread('meatgirl.png')
    large_image = cv2.imread("screenCapture0.png")
    method = cv2.TM_SQDIFF_NORMED
    result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                               large_image.astype(np.float32), method)
    result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                large_image.astype(np.float32), method)
    mn, _, mnLoc, _ = cv2.minMaxLoc(result)
    mn2, _, mnLoc2, _ = cv2.minMaxLoc(result2)
    MPx, MPy = mnLoc
    MPx2, MPy2 = mnLoc2

    xOffset = MPx2 - MPx
    yOffset = MPy2 - MPy

    image = pyautogui.screenshot(region=(0, 250, 1250, 700))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite("screenCapture0.png", image)
    meatboy_image = cv2.imread('meatboy.png')
    meatgirl_image = cv2.imread('meatgirl.png')
    large_image = cv2.imread("screenCapture0.png")
    method = cv2.TM_SQDIFF_NORMED
    result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                               large_image.astype(np.float32), method)
    result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                large_image.astype(np.float32), method)
    mn1, _, mnLoc, _ = cv2.minMaxLoc(result)
    mn21, _, mnLoc2, _ = cv2.minMaxLoc(result2)
    MPx, MPy = mnLoc
    MPx2, MPy2 = mnLoc2

    xOffset1 = MPx2 - MPx
    yOffset1 = MPy2 - MPy

    while abs(xOffset-xOffset1) > 5 and abs(yOffset-yOffset1) > 5:
        xOffset = xOffset1
        yOffset = yOffset1
        image = pyautogui.screenshot(region=(0, 250, 1250, 700))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imwrite("screenCapture" + str(step) + ".png", image)
        meatboy_image = cv2.imread('meatboy.png')
        meatgirl_image = cv2.imread('meatgirl.png')
        large_image = cv2.imread("screenCapture" + str(step) + ".png")
        method = cv2.TM_SQDIFF_NORMED
        result = cv2.matchTemplate(meatboy_image.astype(np.float32),
                                   large_image.astype(np.float32), method)
        result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32),
                                    large_image.astype(np.float32), method)
        mn1, _, mnLoc, _ = cv2.minMaxLoc(result)
        mn21, _, mnLoc2, _ = cv2.minMaxLoc(result2)
        MPx, MPy = mnLoc
        MPx2, MPy2 = mnLoc2

    print '=============================='
    print 'xOffset: ' + str(xOffset)
    print 'yOffset: ' + str(yOffset)

    trows, tcols = meatboy_image.shape[:2]
    trows2, tcols2 = meatgirl_image.shape[:2]

    cv2.rectangle(large_image, (MPx, MPy), (MPx + tcols, MPy + trows),
                  (0, 255, 0), 2)
    cv2.rectangle(large_image, (MPx2, MPy2),
                  (MPx2 + tcols2, MPy2 + trows2), (0, 255, 0), 2)
    cv2.imwrite("screenCapture" + str(step) + ".png", large_image)
    # too low
    if yOffset < 0:
        # too much to the left
        if xOffset > 0:
            print 'jump right'
            nextAction = (step-1) * 4 + 2
        # too much to the right
        else:
            print 'jump left'
            nextAction = (step-1) * 4 + 3
    else:
        # too much to the left
        if xOffset > 0:
            print 'go right'
            nextAction = (step-1) * 4
        # too much to the right
        else:
            print 'go left'
            nextAction = (step-1) * 4 + 1
    print 'Next action: ' + str(nextAction)


actionsBuffer = {}


def model_thread():
    global currentStep, decodingActions, firstSpike, actionsBuffer
    get_first_action()
    print 'Model thread started'
    # wait for SpiNNaker simulation thread to start
    sleep(3)
    for episode in range(numberOfSteps):
        print 'At episode ' + str(episode) + ' in model thread'
        for stepIndex in range(episode+1):
            # if not last step
            if stepIndex != episode:
                # start decoding actions
                decodingActions = True
                currentStep = stepIndex
                # send first spike response for this step
                send_spike('firstSpikeTrigger', first_spike_trigger_connection, stepIndex)
                firstSpike = True
                sleep(0.1)
                decodingActions = False
            else:
                # record best action given by the environment and encode it
                actionsBuffer[stepIndex] = nextAction
                send_spike('stateSpikeInjector', pre_synaptic_spikes_connection, nextAction)
        sleep(1.5)
        execute_commands()
        sleep(1)
        # clear action buffer
        # actionsBuffer[len(actionsBuffer)] holds action suggested by environment
        for actionIndex in range(len(actionsBuffer) - 1):
            actionsBuffer[actionIndex] = -1

        # if didn't finish simulation
        if episode is not numberOfSteps:
            restart_game()


threading.Thread(target=model_thread).start()
sim.run(numberOfSteps * 10000)

sim.end()
