import sys, asyncio
import time
from threading import Thread
import pygame
from queue import Queue
import sdl2.ext
import numpy as np
from classes import Chip8, Screen 
import winsound

debug = False
resolution = (64,32) #wxh colsxrows
factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
sprite = factory.from_image("C:\\Users\\Eman\\Pictures\\Beast_Gohan_Powers_Up.webp")

fontset = np.array([
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80  # F
], dtype=np.uint8)

key_mapping = [
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
    pygame.K_q,pygame.K_w,pygame.K_e, pygame.K_a,
    pygame.K_s,pygame.K_d,pygame.K_r, pygame.K_f,
    pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v
]
video_scale = 10
clock_speed = 1000 #500mhz #delay
refresh_rate = 30
rom_file = ""
#code

def EventHandler(event: pygame.event.Event):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    elif event.type == pygame.KEYDOWN:
        key = event.key
        if key in key_mapping:
            index = key_mapping.index(key)
            if debug:
                print(f"Key: {key} (I: {index}) pressed")
            chip.keypad[index] = 1
    elif event.type == pygame.KEYUP:
        key = event.key
        if key in key_mapping:
            index = key_mapping.index(key)
            if debug:
                print(f"Key: {key} (I: {index}) released")
            chip.keypad[index] = 0


pygame.init()

display = Screen((64,32), video_scale)
display.start()

chip = Chip8()
chip.LoadFontset(fontset)
chip.LoadROM(rom_file)

def display_handler():
    delay_time = 1 / refresh_rate
    
    while True:
        time.sleep(delay_time)
        video_buffer = chip.display_memory
        display.Update(video_buffer)

def timers_handler():
    delay_time = 1 / 60
    frequency = 1000 
    duration = 1  # Set Duration To 1000 ms == 1 second
    #if timer set then decrement
    while True:
        time.sleep(delay_time)
        if chip.delay_timer > 0:
            chip.delay_timer -= 1
        if chip.sound_timer > 0:
            
            winsound.Beep(frequency, duration)
            chip.sound_timer -= 1     

def main():
    delay_time = 1 / clock_speed
    print(f"Rom: {rom_file}")
    print(f"Scale factor: {video_scale} so resolution of {resolution[0]*video_scale}x{resolution[1]*video_scale}")
    print(f"Running at {clock_speed}hz so delay time of {round(delay_time*1000, 1)} ms")
    print(f"Screen refresh rate at {refresh_rate}hz so delay time of {round(1/refresh_rate*1000, 1)} ms")
    first_time: float
    second_time: float
    
    while True:
        if debug:
            first_time = time.perf_counter()
        time.sleep(delay_time)
        
        for event in pygame.event.get():
            EventHandler(event)
        chip.Cycle()

        if debug:
            second_time = time.perf_counter()
            diff_ms = int((second_time - first_time)*1000)
            if diff_ms > 0:
                print(f"it took {diff_ms} ms for cycle. for delay time")

display_thread = Thread(target=display_handler, name="Display Handler")    
timers_thread = Thread(target=timers_handler, name="Timers Handler")
timers_thread.start()
display_thread.start()  
main()

# nibble = 4 bits 0x0
# byte = 8 bits 0x00
#byte = 2 nibbles 
