
from dataclasses import dataclass
import time
import numpy as np
import sys, random, pygame
from threading import Thread
import asyncio 
debug = True
class Buffer:
    def __init__(self):
        self.buffer: list[int] = []
    
    def write(self, data: bytes):
        for byte in data:
            self.buffer.append(byte)
    def writes(self, data: str):
        self.write(bytes(data, encoding='utf8'))
    
    def print_str(self):
        string: str = ""
        for byte in self.buffer:
            string += chr(byte)
        print(string)



class Screen(Thread):
    def __init__(self, resolution: tuple[int,int], scale_factor):
        super(Screen, self).__init__()
        self.scale = scale_factor
        self.screen = pygame.display.set_mode((resolution[0]*self.scale, resolution[1]*self.scale))
        self.screen.fill((0,0,0))
        self.clock = pygame.time.Clock()
        self.clock.tick(30)
        
        self.events = []
    
    def Update(self, buffer):
        on_colour = (255,255,255)  
        off_colour = (0,0,0)
        display_pixel_y = 0
        display_pixel_x = 0
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
    

class Chip8:
    registers = np.zeros((16), np.uint8) #16 8bit registers
    memory  = np.zeros((4096), np.uint8) #4096 bytes of memory
    index_register = np.uint16(0) #16 bit index register
    program_counter = np.uint16(0x200) #16 bit program counter
    stack = np.zeros((16), np.uint16) #16 level stack
    stack_pointer = np.uint8(0) #8bit stack pointer
    delay_timer = np.uint8(0) #8bit delay timer
    sound_timer = np.uint8(0) #8bit sound timer
    keypad = np.zeros((16), np.uint8) #16 8bit input keys
    display_memory = np.zeros((32,64), np.uint8) #64x32 monochrome display. 0 = off, 1 = on
    opcode = np.uint16(0)
    rom_start_addr = np.uint(0x200)
    display_updated = False
    def __init__(self):
        self.output = Buffer()
    
    def LoadFontset(self, fontset):
        print("Loading fontset of size ", len(fontset))
        mem_address = 0x50
        for font in fontset:
            self.memory[mem_address] = font
            mem_address += 1
        self.fontset_start_addr = mem_address

    def LoadROM(self, filename: str):
        size: int
        buffer: bytes
        with open(filename, 'rb') as file:
            buffer = file.read()
            size = len(buffer)
            file.close()

        for i in range(0, size):
            self.memory[self.rom_start_addr + i] = buffer[i]
        print(f"Loaded rom: {size} bytes")
        #available_memory = int(self.memory.all()) - int(self.program_counter.all())
       # if available_memory < size:
         #   print(f"ROM too big! {size}. {available_memory} available!")
         #   return None

    def Cycle(self):
        #fetch
        self.opcode = (self.memory[self.program_counter] << 8) | self.memory[self.program_counter + 1]
        
       # print(f"Fetched opcode: {self.opcode} ({hex(self.opcode)})")
        #self.output.writes(f"Fetched opcode: {self.opcode} ({hex(self.opcode)})")
        #increment pc
        self.program_counter += 2

        #decode and execute
        self.ProcessOC()
        #if timer set then decrement
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
    def ProcessOC(self):
        #first_byte = (self.opcode & 0xFF00) >> 8
        second_byte = (self.opcode & 0x00FF)
        #first_nibble = (self.opcode & 0xF000) >> 12
        second_nibble = (self.opcode & 0x0F00) >> 8 
        third_nibble = (self.opcode & 0x00F0) >> 4
        fourth_nibble = self.opcode & 0xF
       
        match (self.opcode & 0xF000) >> 12: # match first nibble
            case 0x0:
                match self.opcode & 0xF: #match fourth nibble
                    case 0x0:  #0x00E0 CLS Clear display
                        self.display_memory.fill(0)
                    case 0xE:  # 0x00EE RET Return from a subroutine
                        self.stack_pointer = self.stack_pointer - 1
                        self.program_counter = self.stack[self.stack_pointer]
                    case _:
                        print("Unknown 0x0 opcode: ", hex(self.opcode))
            case 0x1:#JP Jump to location 0x1[nnn]
                nnn = self.opcode & 0x0FFF
                self.output.writes(f"Calling subroutine at {nnn}")
                self.program_counter = np.uint16(nnn)
            case 0x2: #CALL call subroutine at 0x2[nnn]
                #add old pc to stack and point to new function
                nnn = self.opcode & 0x0FFF
                self.output.writes(f"Calling subroutine at {nnn}")
                self.stack[self.stack_pointer] = self.program_counter 
                self.stack_pointer += 1
                self.program_counter = nnn
            case 0x3: # SE 0x3xkk if register value at x equals kk then skip
                x = second_nibble
                kk = second_byte
                if self.registers[x] == kk:
                    self.program_counter += 2
            case 0x4: #SNE 0x4xkk opposite of SE
                x = second_nibble
                kk = second_byte
                if self.registers[x] != kk:
                    self.program_counter += 2
            case 0x5: # SE 0x5xy0 if register value at x equals register value at y then skip
                x = second_nibble
                y = third_nibble
                if self.registers[x] == self.registers[y]:
                    self.program_counter += 2
            case 0x6: #LD 0x6xkk set register value at x to kk
                x = second_nibble
                kk = second_byte
                self.registers[x] = kk
            case 0x7: #ADD 0x7xkk add kk to register value at x
                x = second_nibble
                kk = second_byte
                self.registers[x] += kk
            case 0x8:# LD 0x8xy0 
                x = second_nibble
                y = third_nibble 
                match fourth_nibble:
                    case 0x0: #set value at register x to register value y
                        self.registers[x] = self.registers[y]
                    case 0x1: #set value at register x  = register x OR register y
                        self.registers[x] |= self.registers[y]
                    case 0x2: #register x = register x AND register y
                        self.registers[x] &= self.registers[y]
                    case 0x3: #register x = register x XOR register y
                        self.registers[x] ^= self.registers[y]
                    case 0x4: #add register x and y then set registerF to 1 if sum over 255 (8 bits)
                        sum = np.uint16(self.registers[x]) + np.uint16(self.registers[y])
                        self.registers[0xF] = 1 if sum > 255 else 0
                        self.registers[x] = np.uint8(sum & 0xFF)
                    case 0x5: #sub register y from register x then set register 0xF to 1 if no borrow / x > y
                        self.registers[0xF] = 1 if self.registers[x] > self.registers[y] else 0
                        try:
                            self.registers[x] = self.registers[x] - self.registers[y]
                        except:
                            print(f"Register {x}: {self.registers[x]} Register {y}: {self.registers[y]}")
                    case 0x6: #SHR if least-signficiant bit of Rx value is 1 then set 0xF to 1 else 0 then Rx value divide by 2
                        lsb = self.registers[x] & 0x1
                        self.registers[0xF] = lsb
                        self.registers[x] >>= 1 #self.registers[x] /= 2
                    case 0x7:#SUBN if Ry > Rx then set 0xF to 1 else 0 then sub Rx from Ry and store result in Rx
                        self.registers[0xF] = 1 if self.registers[y] > self.registers[x] else 0
                        self.registers[x] = self.registers[y] - self.registers[x]
                    case 0xE: #SHL if most-significant bit of Rx is 1 then set 0xF to 1 else 0 then Rx multiply by 2
                        msb = (self.registers[x] & 0x80) >> 7 
                        self.registers[0xF] = msb
                        self.registers[x] <<= 1
                    case _:
                        print("Unknown 0x8 opcode: ", hex(self.opcode))
            case 0x9:# SNE 9xy0 skip next instruction if Rx != Vy
                x = second_nibble
                y = third_nibble 
                if self.registers[x] != self.registers[y]:
                    self.program_counter += 2
            case 0xA: #LD Annn set Rindex = nnn
                addr = self.opcode & 0x0FFF
                self.index_register = addr
            case 0xB: #Jump to location nnn + R0
                addr = self.opcode & 0xFFF
                self.program_counter = self.registers[0] + addr
            case 0xC: # RND 0xCxkk Rx = random byte AND kk
                x = second_nibble
                kk = second_byte

                self.registers[x] = random.randint(0,255) & kk
            case 0xD: #DRW 0xDxyn Display [n] byte sprite starting at memory location   I at (Rx, Ry), set 0xF = collison
                #sprite always eight pixels wide so [n] = height
                x = second_nibble
                y = third_nibble
                n = fourth_nibble #height
                self.registers[0xF] = 0

                #wrap pos if beyond dimensions. rows = height cols = width
                #cols_count = width rows_count = height
                rows_count, cols_count = self.display_memory.shape
                pos_x = self.registers[x] % cols_count
                pos_y = self.registers[y] % rows_count
                
                for row_num in range(0, n):
                    sprite_byte = self.memory[self.index_register + row_num]

                    for col_num in range(0, 8):
                        sprite_pixel = sprite_byte & (0x80 >> col_num)
                        #pos_y + row_num | current row plus position of sprite 
                        #screen_pixel = self.display_memory[(pos_y+row_num) * cols_count + (pos_x + col_num)]
                        
                        y_idx = pos_y+row_num
                        x_idx = pos_x +col_num
                        #print(y_idx)
                        #print(x_idx)
                        if y_idx > len(self.display_memory)-1 or x_idx > len(self.display_memory[y_idx])-1:
                            continue
                        screen_pixel = self.display_memory[y_idx][x_idx]

                        #sprite pixel XOR screen pixel
                        if sprite_pixel: #on
                            if screen_pixel == 1: #set collision on if screen pixel also on
                                #self.registers[0xF] = 1
                                screen_pixel = 0
                            else:
                                screen_pixel = 1
                            
                            #xor with sprite pixel
                           # screen_pixel ^= sprite_pixel
                        else:
                            if screen_pixel == 1:
                                screen_pixel = 1
                            else:
                                screen_pixel = 0
                        self.display_memory[y_idx][x_idx] = screen_pixel
                        self.display_updated = True
                       # print(sprite_pixel)
            case 0xE: 
                match fourth_nibble:
                    case 0xE: #SKP 0xEx9E skip next instruction if key with the value of Rx is pressed
                        x = second_nibble
                        key = self.registers[x]
                        if self.keypad[key]:
                            self.program_counter += 2
                    case 0x1:#SKNP 0xExA1 skip next instruction if key with the value of Rx is not pressed
                        x = second_nibble
                        key = self.registers[x]
                        if not self.keypad[key]:
                            self.program_counter += 2
                    case _:
                        print("Unknown 0xE opcode: ", hex(self.opcode))
            case 0xF:
                match second_byte:
                    case 0x07: #0xFx07 Rx = delay timer value
                        x = second_nibble
                        self.registers[x] = self.delay_timer
                    case 0x0A: #0xFx0A Wait for key press then store key value in Rx
                        x = second_nibble
                        detected_press = False
                        for idx in range(0, len(self.keypad)-1):
                            if self.keypad[idx]:
                                self.registers[x] = idx
                                detected_press = True
                                break
                        if not detected_press:
                            self.program_counter -= 2 #do this instruction again
                    case 0x15: #Fx15 Set delay timer = Rx
                        x = second_nibble
                        self.delay_timer = self.registers[x]
                    case 0x18: #Fx18 sound timer = Rx
                        x = second_nibble
                        self.sound_timer = self.registers[x]
                    case 0x1E:#Fx1E index = index + Rx
                        x = second_nibble
                        self.index_register += self.registers[x]
                    case 0x29: #Fx29 index = location of sprite for digit Rx
                        x = second_nibble
                        digit = self.registers[x]
                        #font is 5 bytes each and start a fontset start addr
                        #digit = position of font character
                        self.index_register  = self.fontset_start_addr + (5*digit)
                    case 0x33: #Fx33 store bcd representation of Rx in memory location index, +1 and +2
                        # We use the modulus operator to get the right-most digit of a number, 
                        # and then do a division to remove that digit. A division by ten will 
                        # either completely remove the digit (340 / 10 = 34), or result in a float 
                        # which will be truncated (345 / 10 = 34.5 = 34).

                        x = second_nibble
                        value = self.registers[x]
                        #ones place
                        self.memory[self.index_register + 2] = value % 10
                        value /= 10
                        #tens place
                        self.memory[self.index_register + 1] = value % 10
                        value /= 10
                        #hundreds place
                        self.memory[self.index_register] = value % 10
                    case 0x55: #Fx55 store registers from 0 to Rx in memory starting at location index
                        x = second_nibble
                        for idx in range(0, x+1):
                            self.memory[self.index_register + idx] = self.registers[idx]
                    case 0x65: #Fx65 read to registers from 0 to Rx from memory starting at location index
                        x = second_nibble
                        for idx in range(0, x+1):
                            self.registers[idx] = self.memory[self.index_register+idx]
                    case _:
                        print("Unknown 0xF 2nd byte opcode: ", hex(self.opcode))
            case _:
                print("Unknown opcode: ", hex(self.opcode))


        
