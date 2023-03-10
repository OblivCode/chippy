
from dataclasses import dataclass
import time
import numpy as np
import sys, random, pygame
from threading import Thread
import asyncio 


debug = True


class Screen(Thread):
    def __init__(self, resolution: tuple[int,int], scale_factor):
        super(Screen, self).__init__()
        self.scale = scale_factor
        self.screen = pygame.display.set_mode((resolution[0]*self.scale, resolution[1]*self.scale))
        self.clock = pygame.time.Clock()
        self.clock.tick(30)
        
        self.events = []
    
    def Update(self, buffer):
        on_colour = (255,255,255)  
        off_colour = (0,0,0)
        display_pixel_y = 0
        display_pixel_x = 0
        self.screen.fill(off_colour)
        for y in range(0, len(buffer)):
            for x in range(0, len(buffer[y])):
                pixel = buffer[y][x]
                if pixel == 1: #if pixel on
                    pixel_colour = on_colour
                    #print(f"pixel on at {row} {col}")
                else:
                    pixel_colour = off_colour

                pygame.draw.rect(self.screen, pixel_colour, [display_pixel_x, display_pixel_y, self.scale, self.scale])
                display_pixel_x += self.scale
            display_pixel_x = 0
            display_pixel_y += self.scale
        pygame.display.update()
            #self.clock.tick(30)
        #print("Updated {} rows", row_counter+1)
    

   
