import numpy as np
import random
import sys
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
        #self.opcode = np.uint16(self.rom_start_addr)
        print(f"Loaded rom: {size} bytes")

    def Cycle(self):
        #fetch
        self.opcode = (self.memory[self.program_counter] << 8) | self.memory[self.program_counter + 1]
        #increment pc
        self.program_counter += 2
        #decode and execute
        self.ProcessOC()
        
    def ProcessOC(self):       
        updated_chip = OpcodeHandler(self).process()

        self.program_counter = updated_chip.program_counter
        self.opcode = updated_chip.opcode
        self.registers = updated_chip.registers
        self.index_register = updated_chip.index_register
        self.stack_pointer = updated_chip.stack_pointer

        self.display_memory = updated_chip.display_memory
        self.memory = updated_chip.memory
        self.stack = updated_chip.stack

        self.delay_timer = updated_chip.delay_timer
        self.sound_timer = updated_chip.sound_timer

        

class OpcodeHandler:
    def __init__(self, chip: Chip8):
        self.chip = chip
        self.kk = (chip.opcode & 0x00FF)
        self.nnn = chip.opcode & 0x0FFF
        self.w = (chip.opcode & 0xF000) >> 12
        self.x = (chip.opcode & 0x0F00) >> 8 
        self.y = (chip.opcode & 0x00F0) >> 4
        self.z = chip.opcode & 0x000F

        self.Ry = self.chip.registers[self.y]
        self.Rx = self.chip.registers[self.x]
        self.Rindex = self.chip.index_register

    def process(self) -> Chip8:
        match self.w:
            case 0x0:
                if self.x0():
                    print("Unknown 0x0 opcode: ", hex(self.chip.opcode)) 
                    #sys.exit(0)
            case 0x1:
                self.x1()    
            case 0x2: 
                self.x2()  
            case 0x3: 
                self.x3()  
            case 0x4: 
                self.x4()   
            case 0x5:
                self.x5()   
            case 0x6: #LD 0x6xkk set register value at x to kk
                self.x6()               
            case 0x7: 
                self.x7()  
            case 0x8:
               if self.x8():
                    print("Unknown 0x8 opcode: ", hex(self.chip.opcode))  
            case 0x9:
                self.x9()  
            case 0xA:
                self.xA()  
            case 0xB: 
                self.xB()
            case 0xC: 
                self.xC()
            case 0xD: 
                self.xD()
            case 0xE: 
                if self.xE():
                    print("Unknown 0xE opcode: ", hex(self.chip.opcode))  
            case 0xF:
                if self.xF():
                    print("Unknown 0xF opcode: ", hex(self.chip.opcode))  
            case _:
                
                print("Unknown opcode: ", hex(self.chip.opcode))

        return self.chip
            
    
    def x0(self):
        match self.kk:
            case 0xE0:
                self.chip.display_memory.fill(0)
            case 0xEE:
                self.chip.stack_pointer = self.chip.stack_pointer - 1
                self.chip.program_counter = self.chip.stack[self.chip.stack_pointer]
            case _:
                return True
        return False
    def x1(self):#JP Jump to location 0x1[nnn]
        self.chip.output.writes(f"Calling subroutine at {self.nnn}")
        self.chip.program_counter = np.uint16(self.nnn)
    def x2(self): #CALL call subroutine at 0x2[nnn]
        self.chip.output.writes(f"Calling subroutine at {self.nnn}")
        self.chip.stack[self.chip.stack_pointer] = self.chip.program_counter 
        self.chip.stack_pointer += 1
        self.chip.program_counter = self.nnn
    def x3(self):# SE 0x3xkk if register value at x equals kk then skip
        if self.Rx == self.kk:
            self.chip.program_counter += 2
    def x4(self): #SNE 0x4xkk opposite of SE
        if self.Rx != self.kk:
            self.chip.program_counter += 2
    def x5(self):# SE 0x5xy0 if register value at x equals register value at y then skip
        if self.Rx == self.Ry:
            self.chip.program_counter += 2
    def x6(self): #LD 0x6xkk set register value at x to kk
         self.chip.registers[self.x] = self.kk
    def x7(self):#ADD 0x7xkk add kk to register value at x
        self.chip.registers[self.x] += self.kk
    def x8(self):# LD 0x8xy0 
        match self.z:
            case 0x0:
                self.chip.registers[self.x] = self.Ry
            case 0x1: #set value at register x  = register x OR register y
                self.chip.registers[self.x] |= self.Ry
            case 0x2: #register x = register x AND register y
                self.chip.registers[self.x] &= self.Ry
            case 0x3: #register x = register x XOR register y
                self.chip.registers[self.x] ^= self.Ry
            case 0x4: #add register x and y then set registerF to 1 if sum over 255 (8 bits)
                sum = np.uint16(self.Rx) + np.uint16(self.Ry)
                if sum > 255:
                    self.chip.registers[0xF] = 1
                else:
                    self.chip.registers[0xF] = 0
                self.chip.registers[self.x] = np.uint8(sum & 0xFF)
            case 0x5: #sub register y from register x then set register 0xF to 1 if no borrow / x > y
                no_borrow = self.Rx > self.Ry
                #print(f"x: {x} y: {y} Rx: {rx} Ry: {ry} BRW: {not no_borrow} Rx: {self.registers[x]}")
                if no_borrow:
                    self.chip.registers[self.x] = self.Rx- self.Ry
                    self.chip.registers[0xF] = 1
                else:
                    self.chip.registers[self.x] = 255 - (self.Ry - self.Rx)
                    self.chip.registers[0xF] = 0
                        
            case 0x6: #SHR if least-signficiant bit of Rx value is 1 then set 0xF to 1 else 0 then Rx value divide by 2
                lsb = self.chip.registers[self.x] & 0x1
                self.chip.registers[0xF] = lsb
                self.chip.registers[self.x] >>= 1 #self.registers[x] /= 2
            case 0x7:#SUBN if Ry > Rx then set 0xF to 1 else 0 then sub Rx from Ry and store result in Rx
                if self.Ry > self.Rx:
                    self.chip.registers[0xF] = 1 
                else:
                    self.chip.registers[0xF] = 0
                self.chip.registers[self.x] = self.Ry - self.Rx
            case 0xE: #SHL if most-significant bit of Rx is 1 then set 0xF to 1 else 0 then Rx multiply by 2
                msb = (self.chip.registers[self.x] & 0x80) >> 7 
                self.chip.registers[0xF] = msb
                self.chip.registers[self.x] <<= 1   
            case _:
                return True
        return False
    def x9(self): # SNE 9xy0 skip next instruction if Rx != Vy
        if self.Rx != self.Ry:
            self.chip.program_counter += 2
    def xA(self):  #LD Annn set Rindex = nnn
        self.chip.index_register = self.nnn
    def xB(self): #Jump to location nnn + R0
        self.chip.program_counter = self.chip.registers[0] + self.nnn
    def xC(self): # RND 0xCxkk Rx = random byte AND kk
        self.chip.registers[self.x] = random.randint(0,255) & self.kk
    def xD(self): #DRW 0xDxyn Display [n] byte sprite starting at memory location   I at (Rx, Ry), set 0xF = collison
        #sprite always eight pixels wide so self.z = height
        self.chip.registers[0xF] = 0

        #wrap pos if beyond dimensions. rows = height cols = width
        #cols_count = width rows_count = height

        rows_count, cols_count = self.chip.display_memory.shape
        pos_x = self.Rx % cols_count
        pos_y = self.Ry % rows_count

        for row_num in range(0, self.z):
            sprite_byte = self.chip.memory[self.Rindex + row_num]

            for col_num in range(0, 8):
                sprite_pixel = sprite_byte & (0x80 >> col_num)
                y_idx = pos_y+row_num
                x_idx = pos_x+col_num
                        
                if y_idx > len(self.chip.display_memory)-1 or x_idx > len(self.chip.display_memory[y_idx])-1:
                            continue
                screen_pixel = self.chip.display_memory[y_idx][x_idx]
                #sXOR screen pixel
                if sprite_pixel != 0: #on
                    if screen_pixel == 1:
                        self.chip.registers[0xF] = 1
                    screen_pixel ^= 0x1
                self.chip.display_memory[y_idx][x_idx] = screen_pixel
    def xE(self):
        match self.z:
            case 0xE: #SKP 0xEx9E skip next instruction if key with the value of Rx is pressed
                if self.chip.keypad[self.Rx]:
                    self.chip.program_counter += 2
            case 0x1:#SKNP 0xExA1 skip next instruction if key with the value of Rx is not pressed
                if not self.chip.keypad[self.Rx]:
                    self.chip.program_counter += 2
            case _:
                   return True
    def xF(self):
        match self.kk:
            case 0x07: #0xFx07 Rx = delay timer value
                self.chip.registers[self.x] = self.chip.delay_timer
            case 0x0A: #0xFx0A Wait for key press then store key value in Rx
                detected_press = False
                for idx in range(0, len(self.chip.keypad)):
                    if self.chip.keypad[idx]:
                        self.chip.registers[self.x] = idx
                        detected_press = True
                        break
                if not detected_press:
                    self.chip.program_counter -= 2 #do this instruction again
            case 0x15: #Fx15 Set delay timer = Rx
                self.delay_timer = self.Rx
            case 0x18: #Fx18 sound timer = Rx
                self.chip.sound_timer = self.Rx
            case 0x1E:#Fx1E index = index + Rx
                self.chip.index_register += self.Rx
            case 0x29: #Fx29 index = location of sprite for digit Rx
                digit = self.Rx
                #font is 5 bytes each and start a fontset start addr
                #digit = position of font character
                self.chip.index_register  = self.chip.fontset_start_addr + (5*digit)
            case 0x33: #Fx33 store bcd representation of Rx in memory location index, +1 and +2
                # We use the modulus operator to get the right-most digit of a number, 
                # and then do a division to remove that digit. A division by ten will 
                # either completely remove the digit (340 / 10 = 34), or result in a float 
                # which will be truncated (345 / 10 = 34.5 = 34).

                value = self.Rx
                #ones place
                self.chip.memory[self.Rindex + 2] = value % 10
                value /= 10
                #tens place
                self.chip.memory[self.Rindex + 1] = value % 10
                value /= 10
                #hundreds place
                self.chip.memory[self.Rindex] = value % 10
            case 0x55: #Fx55 store registers from 0 to Rx in memory starting at location index
                for idx in range(0, self.x+1):
                    self.chip.memory[self.Rindex + idx] = self.chip.registers[idx]
            case 0x65: #Fx65 read to registers from 0 to Rx from memory starting at location index
                for idx in range(0, self.x+1):
                    self.chip.registers[idx] = self.chip.memory[self.Rindex+idx]
            case _:
                return True
        return False
