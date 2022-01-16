import binascii
import sys
import queue
from dataclasses import dataclass

def signed( value ):
  if value & 0x80000000:
    twos_complement = ~value + 1
    return -( twos_complement & 0xFFFFFFFF )
  return  value

def sext(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

instructiuni = bytearray()
empty4Bytes = bytearray(binascii.unhexlify("00000000"))
eip = 0

registrii = [
    0,  # Zero Index 0
    0,  # ra (Return Adress) Index 1
    0,  # sp (Stack pointer) Index 2
    0,  # gp (Global pointer) Index 3
    0,  # tp(Thread pointer) Index 4
    0,  # t0 (Temporary/alternate return address) Index 5
    0,  # t1 (Temporary) Index 6
    0,  # t2 (Temporary) Index 7
    0,  # s0/fp (Saved register/frame pointer) Index 8
    0,  # s1 (Saved register) Index 9
    0,  # a0 (Function argument/return value) Index 10
    0,  # a1 (Function argument/return value) Index 11
    0,  # a2 (Function argument) Index 12
    0,  # a3 (Function argument) Index 13
    0,  # a4 (Function argument) Index 14
    0,  # a5 (Function argument) Index 15
    0,  # a6 (Function argument) Index 16
    0,  # a7 (Function argument) Index 17
    0,  # s2 (Saved register) Index 18
    0,  # s3 (Saved register) Index 19
    0,  # s4 (Saved register) Index 20
    0,  # s5 (Saved register) Index 21
    0,  # s6 (Saved register) Index 22
    0,  # s7 (Saved register) Index 23
    0,  # s8 (Saved register) Index 24
    0,  # s9 (Saved register) Index 25
    0,  # s10 (Saved register) Index 26
    0,  # s11 (Saved register) Index 27
    0,  # t3 (Temporary) Index 29
    0,  # t4 (Temporary) Index 30
    0,  # t5 (Temporary) Index 31
    0,  # t6 (Temporary) Index 32
]


def instructionFetchGenerator():
    global instructiuni
    global eip

    lungime = len(instructiuni)
    while eip < lungime:
        try:
            yield (instructiuni[eip] << 24) | (instructiuni[eip + 1] << 16) | (
                    instructiuni[eip + 2] << 8) | instructiuni[eip + 3]  # reconstruim instructiunea cu cei 4 bytes
            eip += 4
        except:
            break


def instructionProcessing(instructiune):
    global eip
    instructiune = bytearray(instructiune.to_bytes(4, "little"))
    opcode = instructiune[0] & 0b1111111
    instructiune = int.from_bytes(instructiune, "little")
    if instructiune == 0b1110011:                       #ecall
        #print("ecall")
        ECALL()
    elif instructiune == 0b100000000000001110011:       #ebreak
        EBREAK()
    elif opcode == 0:
        eip += 4
    elif opcode == 0b0110111:
        #print("Merge in LUI")
        instr_LUI(instructiune)
    elif opcode == 0b0010111:
        #print("Merge in AUIPC")
        instr_AUIPC(instructiune)
    elif opcode ==0b1101111:
        #print("Merge in JAL")
        instr_JAL(instructiune)
    elif opcode == 0b1100111:
        #print("Merge in JARL")
        instr_JARL(instructiune)
    elif opcode == 0b110011:
        #print("Merge in R")
        instructiune_R(instructiune)
    elif opcode == 0b1100111 or opcode == 0b11 or opcode == 0b10011:
        #print("Merge in I")
        instructiune_I(instructiune, opcode)
    elif opcode == 0b100011:
        #print("Merge in S")
        instructiune_S(instructiune)
    elif opcode == 0b1100011:
        #print("Merge in B")
        instructiune_B(instructiune)
    else:
        #print("Instructiune negasita", bin(opcode), hex(instructiune), eip // 4)
        eip += 4

def ECALL():
    pass

def EBREAK():
    pass

def instr_LUI(instructiune):
    #print("A ajuns in LUI")
    rd = (instructiune >> 7) & 0b11111
    #print("rd = ", rd)
    offset = (instructiune >> 12) & 0b1111111111111111111
    registrii[rd] = (sext(offset << 12, 20)) & 0xFFFFF
    global eip
    eip += 4


def instr_AUIPC(instructiune):
    #print("A ajuns in AUIPC")
    global eip
    rd = (instructiune >> 7) & 0b11111
    offset = (instructiune >> 12) & 0b11111111111111111111
    opcode = instructiune & 0b1111111
    registrii[rd] = eip + sext((offset << 12), 32) & 0xFFFFF
    eip += 4

def instr_JAL(instructiune):
    #print("A ajuns in JAL")
    global eip
    rd = (instructiune >> 7) & 0b11111
    offset = (instructiune >> 12) & 0b11111111111111111111
    opcode = instructiune & 0b1111111
    if rd != 0:
        registrii[rd] = eip + 4
    eip += offset

def instr_JARL(instructiune):
    #print("A ajuns in JARL")
    global eip
    funct3 = (instructiune >> 12) & 0b111
    rs1 = (instructiune >> 15) & 0b11111
    offset = (instructiune >> 25) & 0b111111111111
    rd = (instructiune >> 7) & 0b11111
    t = eip +4
    eip = (registrii[rs1] + offset) & (not 1)
    registrii[rd] = t

# ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND
def instructiune_R(instructiune):

    rd = (instructiune >> 7) & 0b1111111
    funct3 = (instructiune >> 12) & 0b111
    rs1 = (instructiune >> 15) & 0b11111
    rs2 = (instructiune >> 20) & 0b11111
    funct7 = (instructiune >> 25) & 0b1111111

    if funct3 == 0b000:
        if funct7 == 0b0000000:  # add
            registrii[rd] = (registrii[rs1] + registrii[rs2]) & 0xFFFFFFFF
        elif funct7 == 0b010000:  # sub
            registrii[rd] = registrii[rs1] - registrii[rs2]

    elif funct3 == 0b001:
        if funct7 == 0b0000000:  # sll
            registrii[rd] = (registrii[rs1] << registrii[rs2]) & 0xFFFFFFFF

    elif funct3 == 0b010:
        if funct7 == 0b0000000:  # slt
            registrii[rd] = 1 if registrii[rs1] < signed(registrii[rs2]) else 0

    elif funct3 == 0b011:  # sltu
        if funct7 == 0b0000000:
            registrii[rs2] += 2 ** 32
            registrii[rd] = 1 if registrii[rs1] < registrii[rs2] else 0
    elif funct3 == 0b100:
        if funct7 == 0b0000000:  # xor
            registrii[rd] = registrii[rs1] ^ registrii[rs2]

    elif funct3 == 0b101:
        if funct7 == 0b0000000:  # srl
            registrii[rd] = (registrii[rs1] << registrii[rs2]) & 0xFFFFFFFF
        elif funct7 == 0b0100000:  # sra
            registrii[rd] = registrii[rs1] >> signed(registrii[rs2])
    elif funct3 == 0b110:  # or
        if funct7 == 0b0000000:
            registrii[rd] = registrii[rs1] or registrii[rs2]
    elif funct3 == 0b111:  # and
        if funct7 == 0b0000000:
            registrii[rd] = registrii[rs1] and registrii[rs2]
    global eip
    eip += 4


# JARL, LB, LH, LW, LBU, LHU, ADDI, SLLI, SLTI, XORI, SRLI, SRAI, ORI, ANDI
def instructiune_I(instructiune, opcode):
    funct3 = (instructiune >> 12) & 0b111
    rs1 = (instructiune >> 15) & 0b11111
    offset = (instructiune >> 20) & 0b111111111111
    rd = (instructiune >> 7) & 0b11111
    #print("In intructiune_I: instructiune = ", bin(instructiune), "   opcode = ", bin(opcode))
    #print("In intructiune_I: ",  "rs1 = ", rs1, "     rd = ", rd, "    offset = ", offset, "     funct3 = ", bin(funct3))
    global eip

    if opcode == 0b0000011:
        if funct3 == 0b000:  # lb
            if rd != 0:
                registrii[rd] = (registrii[rs1] + offset  ) & 0b11111111
                #print("In if1 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b001:  # lh
            if rd != 0:
                registrii[rd] = (registrii[rs1] + offset ) & 0b1111111111111111
                #print("In if2 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset,"     funct3 = ", bin(funct3))
        elif funct3 == 0b010:  # lw
            registrii[rd] = (registrii[rs1] + offset) & 0b11111111111111111111111111111111
            #print("In if3 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b000:  # lbu
            registrii[rd] = (registrii[rs1] + offset ) & 0b11111111
            #print("In if4 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b101:  # lhu
            registrii[rd] = (registrii[rs1] + offset ) & 0b1111111111111111
            #print("In if5 ajunge: rd, rs1 = ", rd,", ", rs1,  "   registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))

    elif opcode == 0b0010011:
        if funct3 == 0b000:  # addi
            if rd != 0:
                registrii[rd] = (registrii[rs1] + sext(offset, 12) ) & 0xFFFFFFFF
                #print("In if6 ajunge: rd, rs1 = ", rd,",", rs1,  "   registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b001:  # slli
            shamt = (offset & 0b11111)
            registrii[rd] = (registrii[rs1] << shamt) & 0xFFFFFFFF
            #print("In if7 ajunge: rd, rs1 = ", rd,",", rs1,  "   registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b010:  # slti
            registrii[rd] = registrii[rs1] < (offset)
            #print("In if8 ajunge: rd, rs1 = ", rd,",", rs1,  "   registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b100:  # xori
            registrii[rd] = registrii[rs1] ^ offset
            #print("In if9 ajunge: rd, rs1 = ", rd,", ", rs1,  "   registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b101:
            if (instructiune >> 30) & 0b1 == 0b0:  # srli
                shamt = (offset & 0b11111)
                registrii[rd] = (registrii[rs1] >> shamt ) & 0xFFFFFFFF
                #print("In if10 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
            elif (instructiune >> 30) & 0b1 == 0b1:  # srai
                shamt = (offset & 0b11111)
                registrii[rd] = (registrii[rs1] >> shamt) & 0xFFFFFFFF
                #print("In if11 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b110:  # ori
            if rd != 0:
                registrii[rd] = registrii[rs1] | sext(offset, 12)
                #print("In if12 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
        elif funct3 == 0b111:  # andi
            registrii[rd] = registrii[rs1] & (offset)
            #print("In if13 ajunge: rd, rs1 = ", rd,", ", rs1,  "registrii[rd] = ", registrii[rd] , "   offset = " , offset, "     funct3 = ", bin(funct3))
    #print(registrii)
    eip += 4


# SB, SH, SW
def instructiune_S(instructiune):

    func3 = instructiune >> 12
    func3 = func3 & 0b111

    # rs1 = (instructiune[1] << 1) + (instructiune[2] >> 7)
    rs1 = instructiune >> 15
    rs1 = rs1 & 0b11111

    rs2 = instructiune >> 20
    rs2 = rs2 & 0b11111

    offset = ((instructiune >> 7) & 0b11111) + ((instructiune >> 25) << 5)

    global eip

    # selectare operatie si executare
    if func3 == 0b000:  # sb
        registrii[(rs1 + offset)] = registrii[rs2] & 0b11111111
    if func3 == 0b001:  # sh
        registrii[(rs1 + offset) ] = registrii[rs2] & 0b1111111111111111
    if func3 == 0b010:  # sw
        registrii[(rs1 + offset) ] = registrii[rs2] & 0b11111111111111111111111111111111

    eip += 4


# BEQ, BNE, BLT, BGE, BLTU, BGEU
def instructiune_B(instructiune):

    func3 = instructiune >> 12
    func3 = func3 & 0b111

    # rs1 = (instructiune[1] << 1) + (instructiune[2] >> 7)
    rs1 = instructiune >> 15
    rs1 = rs1 & 0b11111

    rs2 = instructiune >> 20
    rs2 = rs2 & 0b11111

    offset = ((instructiune >> 8) & 0b1111) + (((instructiune >> 25) & 0b111111) << 4) + (
            ((instructiune >> 7) & 0b1) << 10) + (((instructiune >> 31) & 0b1) << 11)
    global eip

    # selectare operatie si executare
    if func3 == 0b000:
        # beq
        if rs1 == rs2:
            eip += offset
            print("eip in B1 = ", eip)
            return
    elif func3 == 0b001:
        # bne
        if rs1 != rs2:
            eip += offset - offset%4
            #print("eip in B2 = ", eip)
            #print("offset in B2 = ", bin(offset))
            #print("instructiune faulty = ", hex(instructiune))                  #0b100110011101110001001001100011,              0x26771263
            return

    elif func3 == 0b100:
        # blt
        if rs1 < rs2:
            eip += offset
            #print("eip in B3 = ", eip)
            return

    elif func3 == 0b101:
        # bge
        if rs1 >= rs2:
            eip += offset
            #print("eip in B4 = ", eip)
            return
    elif func3 == 0b110:
        # bltu
        # unsigned comparison
        if rs1 > rs2:
            eip += (offset ) & 0xFFFFFFFF
            #print("eip in B5 = ", eip)
            return
    else:  # func3 == 0b111
        # bgeu
        if rs1 <= rs2:
            eip += (offset ) & 0xFFFFFFFF
            #print("eip in B6 = ", eip)
            return
    print("eip in B7 = ", eip)
    eip += 4

s1= sys.argv[1]
with open(s1) as f:
    f.readline()  # Sarim peste prima linie

    adresaAnterioara = 0

    for linie in f:
        if linie[0].isupper():
            continue
        if "<" in linie:  # Sarim peste etichete
            continue
        adresaCurenta = int(linie.split()[0].rstrip(":"), 16)
        adresaCurenta -= 0x80000000

        if adresaCurenta - adresaAnterioara > 4:
            adresaAnterioara += 4
            while adresaAnterioara < adresaCurenta:
                adresaAnterioara += 4
                instructiuni.extend(empty4Bytes)

        adresaAnterioara = adresaCurenta

        instructiuni.extend(bytearray(binascii.unhexlify(linie.split()[1])))  # adaugam cei 4 bytes
    # print(*instructiuni)

    instructionFetcher = instructionFetchGenerator()
    for instructiune in instructionFetcher:
        instructionProcessing(instructiune)

    # for index, registru in enumerate(registrii):
    #     print("Registru {}: {}".format(index, bin(registru)))