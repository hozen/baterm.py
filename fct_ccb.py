# This file provides the CCB board FCT process
# -*- coding: utf-8 -*-
import time
import os
import serial

class FCTCCB:
    def __init__(self, instance, hmi_port, scada_port, uart0_port, en_print):
        self.cali = instance   
        self.hmi_port = hmi_port
        self.scada_port = scada_port
        self.uart0_port = uart0_port
        self.en_print = en_print
        
        # CCB firmware set the slave id to 1 for 3 kinds of MODBUS ports.
        self.slave_id = 1
        
        # error code
        self.FT_USB_AND_RESET_KEY   = 0x1000
        self.FT_HMI                 = 0x2000
        self.FT_DI                  = 0x3000
        self.FT_AI                  = 0x4000
        self.FT_FRAM                = 0x5000
        self.FT_DO                  = 0x6000
        self.FT_UART0               = 0x7000
        self.FT_SCADA               = 0x8000
        self.FT_ETHERNET            = 0x9000
        self.FT_ROTARY_AND_DIP      = 0xA000
        
        self.SUBFT_MD_OK            = self.cali.MD_OK
        self.SUBFT_MD_NO_RESPONSE   = self.cali.MD_NO_RESPONSE
        self.SUBFT_MD_EXCEPTION     = self.cali.MD_EXCEPTION
        self.SUBFT_MD_UNEXPECTED    = self.cali.MD_UNEXPECTED
        self.SUBFT_SPI_UNEXPECTED   = 0X0004
        self.SUBFT_UNEXPECTED       = 0x0005
        
        self.ft_list = []
                         
        # CCB MODBUS address
        self.MB_TEST_FRAM_DATA1 = 0x0001
        self.MB_TEST_FRAM_DATA2 = 0x0002
        self.MB_TEST_FRAM_DATA3 = 0x0003
        self.MB_TEST_FRAM_DATA4 = 0x0004            
        self.MB_DO              = 0x0005         
        self.MB_MULTI_CHANNEL   = 0x0006
        self.MB_LED_OUTPUT      = 0x0007
        
        self.MB_READ_FRAM_DATA1     = 0x0065
        self.MB_READ_FRAM_DATA2     = 0x0066
        self.MB_READ_FRAM_DATA3     = 0x0067
        self.MB_READ_FRAM_DATA4     = 0x0068    
        self.MB_DI                  = 0x0069
        self.MB_DIP_ROTARY          = 0x006A
        self.MB_AI1                 = 0x006B
        self.MB_AI2                 = 0x006C
        self.MB_AI3                 = 0x006D
        self.MB_SPI_AI              = 0x006E
        self.MB_PRODUCT_VER         = 0x006F
        self.MB_FIRMWARE_VER        = 0x0070
        self.MB_FCT_HARDWARE_VER    = 0x0071
        self.MB_FCT_FIRMWARE_VER    = 0x0072
        self.MB_ETHERNET_TEST_FLAG  = 0x0073
        
        self.if_delay = 0
        
        if os.name == 'posix' :
            # Initialize for DI board which should connect to J1 and J2. GA00~02 GB02~04 are used.
            opcode = ((self.cali.SPI_U6_CS & 0x07) << 1) | 0x40  
            self.cali.mcp_spi_write(opcode, self.cali.SPI_IODIRA, 0xFF)
            self.cali.mcp_spi_write(opcode, self.cali.SPI_IODIRB, 0xFF)
                        
            # Initialize for DO board which should connect to J3
            # Initialize DO pins to default value 0 low level
            opcode = ((self.cali.SPI_U7_CS & 0x07) << 1) | 0x40   
            self.cali.mcp_spi_write(opcode, self.cali.SPI_IODIRA, 0x0F)
            self.cali.mcp_spi_write(opcode, self.cali.SPI_IODIRB, 0x00)                                   
        
        if self.if_delay:
            self.delay()
            
        self.run()
        
    def delay(self):
        self.cali.condition.acquire()                    
        try:                 
            self.cali.condition.wait()
            self.cali.condition.release()
        except: 
            print "CCB FCT condition wait error.."
        
    def set_console_instruction_text(self, ret_val, description):          
        if(ret_val):
            self.cali.set_instruction(description +"Fail. Error code %x" %ret_val)    
            self.cali.set_console_text(description +"Fail. Error code %x" %ret_val)    
        else:
            self.cali.set_instruction(description +"Pass.")  
            self.cali.set_console_text(description +"Pass.")    
                              
    # Active FCT mode in fixture when release, this function just for debug.
    def set_fct_mode(self, stepnumber):     
        ret_val = 0                     
        opcode = ((self.cali.SPI_U7_CS & 0x07) << 1) | 0x40   
        gpiob_value = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOB)  
        # GB16
        self.cali.mcp_spi_write(opcode, self.cali.SPI_GPIOB, gpiob_value & 0xBF)   
        gpiob_value = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOB)   
        self.set_console_instruction_text(ret_val, "Step%d: Set CCB board to FCT mode "%stepnumber)
        if self.if_delay:
            self.delay()
        return ret_val
                
    def test_hmi(self, stepnumber):         
        ret_val = 0       
        (ret_status, fct_fw_ver) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, self.MB_FCT_FIRMWARE_VER, 1)                  
            
        if (ret_status != self.SUBFT_MD_OK):
            ret_val = self.FT_HMI + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        else:                  
            self.cali.set_console_text("FCT Firmware version is %x" %fct_fw_ver)    
            #if ((fct_fw_ver&0xFF) == 0x0000):
            #    ret_val = self.FT_HMI + self.SUBFT_UNEXPECTED
            #    self.ft_list.append(hex(ret_val).lstrip("0x"))
                        
        self.set_console_instruction_text(ret_val, "Step%d: CCB HMI communication "%stepnumber)    
        if self.if_delay:
            self.delay()               
        return ret_val
        
    def test_di(self, stepnumber):      
        ret_val = 0     
        expect_di = [0x3F, 0x00]    # the relay board channel 7 broken, so use 0x2f replace of 0x3f [0x3F, 0x00];   #CCB DI0~DO5
        set_spi_ga = [0x50, 0x00]   # Rasp:GA14~GA17;  DO:pin1,2,3,4;  CCB:DI0-,0+,1-,1+
        set_spi_gb = [0x0F, 0x00]   # Rasp:GB10~13;    DO:pin5,6,7,8;  CCB:DI2,3,4,5
        
        for i in range(0,2):
            # write IO board digital output 8 channels, 2 differential and 6 single 
            if os.name == 'posix' :
                opcode = ((self.cali.SPI_U7_CS & 0x07) << 1) | 0x40   
                self.cali.mcp_spi_write(opcode, self.cali.SPI_GPIOA, set_spi_ga[i])                 
                self.cali.mcp_spi_write(opcode, self.cali.SPI_GPIOB, set_spi_gb[i]) 
                
                # Read back and Valid.
                gpioa = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOA) 
                gpiob = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOB) 
                if ((gpioa != set_spi_ga[i]) or (gpiob != set_spi_gb[i])):
                    ret_val = self.FT_DI + self.SUBFT_SPI_UNEXPECTED
                    self.ft_list.append(hex(ret_val).lstrip("0x"))
                    self.cali.set_console_text("test_di: FCT read back GPIOA/B value %x %x != set value %x %x" %(gpioa, gpiob, set_spi_ga[i],set_spi_gb[i]))
                    #break             
        
            time.sleep(0.4)   
            # read CCB board digital input 
            (ret_status, get_md_di) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, self.MB_DI, 1)                   
            if (ret_status != self.SUBFT_MD_OK):
                ret_val = self.FT_DI + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                #break           
                    
            # check DI0~5    
            if(expect_di[i] != (get_md_di & 0x3F)):
                ret_val = self.FT_DI + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_di: FCT expect DO value %x != CCB DI value %x" %(expect_di[i], (get_md_di & 0x3F)))
                #break             
                    
        self.set_console_instruction_text(ret_val, "Step%d: CCB Digital input test "%stepnumber)   
        return ret_val  
    
    def test_ai(self, stepnumber):      
        ret_val = 0        
        coefi2v = (3.2-0.64)/(20-4)     # V/mA
        mcp_coefadc = 4096/3.3          #(2^12)/(Vhref - Vlref)
        ext_coefadc = 4096/3.8          #(2^12)/(Vhref - Vlref)
        expect_current = [20, 12, 4]    #mA
        md_ai_addr = [self.MB_AI1, self.MB_AI2, self.MB_AI3, self.MB_SPI_AI]
        for current in expect_current:
            for i in range(0,4):
                #fct_di = int((current - 4) * 4096)              # (i-4)*(2^12/(20-4))<<4    # select 4~20mA
                fct_di = (int((current* 4096 * 16)/24) & 0xFFF0) # (i)  *(2^12/(24-0))<<4    # select 0~24mA
                if (i == 3): # CCB Board SPI_AI
                    expect_dout = current*coefi2v*ext_coefadc
                else:
                    expect_dout = current*coefi2v*mcp_coefadc

                if os.name == 'posix' :
                    self.cali.dac_spi_write(i + self.cali.dac_start_id, self.cali.DAC_ADDR_DATA, current)
                
                    readdata = self.cali.dac_spi_readback(i + self.cali.dac_start_id, self.cali.DAC_READBACK_DATA) 
                    if (readdata != fct_di) :
                        ret_val = self.FT_AI + self.SUBFT_SPI_UNEXPECTED
                        self.ft_list.append(hex(ret_val).lstrip("0x"))
                        self.cali.set_console_text("test_ai: FCT AO%d, FCT read back value %x != set value %x" %(i, readdata, fct_di))
                        if (self.en_print):
                            print("test_ai: FCT AO%d, FCT read back value %x != set value %x" %(i, readdata, fct_di))
                        #break             
                
                time.sleep(0.2)
                # read CCB board analog input 
                (ret_status, get_md_ai) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, md_ai_addr[i], 1)   
                if (ret_status != self.SUBFT_MD_OK):
                    ret_val = self.FT_AI + ret_status
                    self.ft_list.append(hex(ret_val).lstrip("0x"))
                    #break           
        
                if ((get_md_ai > expect_dout * 1.05) or (get_md_ai < expect_dout * 0.95)):
                    ret_val = self.FT_AI + self.SUBFT_UNEXPECTED
                    self.ft_list.append(hex(ret_val).lstrip("0x"))
                    self.cali.set_console_text("test_ai: CCB AI%d value %d out of 5 percent of FCT expect value %d" %(i, get_md_ai, expect_dout))
                    if (self.en_print):
                        print("test_ai: FCT AO%d, write current %dmA, fct_di is 0x%x, expect_dout is 0x%x"%(i, current, fct_di, expect_dout))
                        print("test_ai: CCB AI%d value 0x%x out of 5 percent of FCT expect value 0x%x" %(i, get_md_ai, expect_dout))
                    #break   
                i = i + 1            
        self.set_console_instruction_text(ret_val, "Step%d: CCB Test analog input "%stepnumber)   
        return ret_val 
              
    def test_fram(self, stepnumber):    
        ret_val = 0  
        test_data = [0x1111, 0x5555, 0xAAAA, 0xFFFF]    
                                           
        # multiple write          
        (ret_status, response)  = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_MULTI_WRITE, self.MB_TEST_FRAM_DATA1, test_data, len(test_data))  
        if(ret_status != self.SUBFT_MD_OK) :
            ret_val = self.FT_FRAM + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        time.sleep(0.2)
        
        (ret_status, md_read_fram) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, self.MB_READ_FRAM_DATA1, 4) 
        if(ret_status != self.SUBFT_MD_OK) :
            ret_val = self.FT_FRAM + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        test_data_str = ''
        for item in test_data:
            test_data_str += hex(item).lstrip("0x")
        
        if(md_read_fram != test_data_str):
            ret_val = self.FT_FRAM + self.SUBFT_UNEXPECTED
            self.ft_list.append(hex(ret_val).lstrip("0x"))
            self.cali.set_console_text("test_fram: Read value %s != internal setting value %s" %(md_read_fram, test_data_str))     
          
        self.set_console_instruction_text(ret_val, "Step%d: CCB EEPROM test "%stepnumber)    
        return ret_val
            
    def test_fram_singal_write(self, stepnumber):    
        ret_val = 0  
        test_data = [0x1111, 0x5555, 0xAAAA, 0xFFFF]       
           
        # single write
        i = 0
        for item in test_data:
            (ret_status, response)  = self.cali.modbus_command(self.hmi_port, self.slave_id, self.MB_CODE_SINGLE_WRITE, (self.MB_TEST_FRAM_DATA1 + i), item)  
            if(ret_status != self.SUBFT_MD_OK) :
                ret_val = self.FT_FRAM + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                #break            
            time.sleep(0.2)
            
            (ret_status, md_read_fram) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.MB_CODE_READ, (self.MB_READ_FRAM_DATA1 + i), 1) 
            if(ret_status != self.SUBFT_MD_OK) :
                ret_val = self.FT_FRAM + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                #break
            
            i = i + 1
            if(md_read_fram != item):
                ret_val = self.FT_FRAM + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_fram: Read value %x != internal setting value %x" %(md_read_fram, item))
                #break                                
                              
        self.set_console_instruction_text(ret_val, "Step%d: CCB EEPROM test "%stepnumber)    
        return ret_val
    
    def test_do_single_board(self, stepnumber):            
        ret_val = 0       
        set_md_do = [0xC0, 0xFF]   # DO0~DO5
        expect_do = [0xFF, 0xC0]   # MODBUS send 0 will output high level, modify it according to set_md_do. expect_do = ~set_md_do
        i = 0
         
        for item in set_md_do:
            # write CCB board digital output
            (ret_status, response) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_SINGLE_WRITE, self.MB_DO, item)                
            if (ret_status != self.SUBFT_MD_OK):
                ret_val = self.FT_DO + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                #break
            # read IO board digital input
            if os.name == 'posix' :
                opcode = ((self.cali.SPI_U6_CS & 0x07) << 1) | 0x40   
                get_spi_di = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOA) 
            else:
                get_spi_di = expect_do[i]
                    
            # check DI0~5  		  
            if((expect_do[i] & 0x3F) != (get_spi_di & 0x3F)):
                ret_val = self.FT_DO + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_do: FCT read DI value %x != CCB DO value %x" %((get_spi_di & 0x3F), (expect_do[i] & 0x3F)))
                #break           
            i = i + 1

        self.set_console_instruction_text(ret_val, "Step%d: CCB Digital output test "%stepnumber)    
        return ret_val
          
    def test_do(self, stepnumber):            
        ret_val = 0       
        set_md_do = [0xC0, 0xFF]   # DO0~DO5
        expect_ga = [0x07, 0x00]   # MODBUS send 0 will output high level, modify it according to set_md_do. expect_do = ~set_md_do
        expect_gb = [0x1C, 0x00]
        i = 0
         
        for item in set_md_do:
            # write CCB board digital output
            (ret_status, response) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_SINGLE_WRITE, self.MB_DO, item)                
            if (ret_status != self.SUBFT_MD_OK):
                ret_val = self.FT_DO + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                #break    
 
            time.sleep(0.2)

            # read IO board digital input
            if os.name == 'posix' :
                opcode = ((self.cali.SPI_U6_CS & 0x07) << 1) | 0x40   
                get_spi_di_ga = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOA) 
                get_spi_di_gb = self.cali.mcp_spi_read(opcode, self.cali.SPI_GPIOB) 
            else:
                get_spi_di_ga = expect_ga[i]
                get_spi_di_gb = expect_gb[i]
                    
            # check DI0~5            
            if((expect_ga[i] & 0x07) != (get_spi_di_ga & 0x07)):
                ret_val = self.FT_DO + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_do: FCT read DI0~2 value %d != CCB DO0~2 value %d" %((get_spi_di_ga & 0x07), (expect_ga[i] & 0x07)))
                print("test_do: FCT read DI0~2 value %d != CCB DO0~2 value %d" %((get_spi_di_ga ), (expect_ga[i] )))
                #break                  
            if((expect_gb[i] & 0x1C) != (get_spi_di_gb & 0x1C)):
                ret_val = self.FT_DO + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_do: FCT read DI3~5 value %d != CCB DO3~5 value %d" %((get_spi_di_gb & 0x1C), (expect_gb[i] & 0x1C)))
                print("test_do: FCT read DI3~5 value %d != CCB DO3~5 value %d" %((get_spi_di_gb), (expect_gb[i])))
                #break           
            i = i + 1

        self.set_console_instruction_text(ret_val, "Step%d: CCB Digital output test "%stepnumber)    
        return ret_val       
       
    def test_uart0(self, stepnumber):     
        ret_val = 0    
        valid_data = 5          
        (ret_status, response) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_SINGLE_WRITE, self.MB_MULTI_CHANNEL, 1)                    
        if (ret_status != self.SUBFT_MD_OK):
            ret_val = self.FT_UART0 + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
                    
        (ret_status, response) = self.cali.modbus_command(self.uart0_port, self.slave_id, self.cali.MB_CODE_DIAGNOSTIC , self.cali.MB_SUBCODE_QUERY, valid_data)               
        if (ret_status != self.SUBFT_MD_OK):
            ret_val = self.FT_UART0 + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        
        if(response != valid_data) :
            ret_val = self.FT_UART0 + self.SUBFT_UNEXPECTED
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        
        self.set_console_instruction_text(ret_val, "Step%d: CCB UART0 communication test "%stepnumber)   
        return ret_val
        
    def test_scada(self, stepnumber):      
        ret_val = 0    
        valid_data = 5                
        (ret_status, response) = self.cali.modbus_command(self.scada_port, self.slave_id, self.cali.MB_CODE_DIAGNOSTIC, self.cali.MB_SUBCODE_QUERY, valid_data)                
        if (ret_status != self.SUBFT_MD_OK):
            ret_val = self.FT_UART0 + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        
        if(response != valid_data) :
            ret_val = self.FT_SCADA + self.SUBFT_UNEXPECTED
            self.ft_list.append(hex(ret_val).lstrip("0x"))
        
        self.set_console_instruction_text(ret_val, "Step%d: CCB SCADA communication test "%stepnumber)   
        return ret_val  
            
    def test_rotary_switch_and_DIP_switch_inputs(self, stepnumber):    
        ret_val = 0   
        expect_rotary_switch = [11,0]
        expect_DIP_switch = [0xFF,0]
        instruction_str = ["1. Set rotary and DIP switch on CCB as below manually.\nThen, press the pass button on GUI to continue the test.\n1. 按下图所示手动设置旋转开关和拨码开关.\n然后，点击界面上的“Pass 通过”按钮继续测试.",                                                                                                
                           "2. Reset rotary and DIP switch on CCB as below manually.\nThen, press the pass button on GUI to continue the test.\n2. 按下图所示手动设置旋转开关和拨码开关.\n然后，点击界面上的“Pass 通过”按钮继续测试."]
        tutorial_name = ["switches1.jpg","switches2.jpg"]
        for i in range(0,2):
            self.cali.set_instruction(instruction_str[i])  
            self.cali.set_tutorial(tutorial_name[i])
            self.delay()
               
            (ret_status, switches) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, self.MB_DIP_ROTARY, 1)                 
            if (ret_status != self.SUBFT_MD_OK):
                ret_val = self.FT_ROTARY_AND_DIP + ret_status
                self.ft_list.append(hex(ret_val).lstrip("0x"))
            
            if((((switches&0xFF00)>>8) != expect_rotary_switch[i]) or ((switches&0xFF) != expect_DIP_switch[i]) ):
                ret_val = self.FT_ROTARY_AND_DIP + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                self.cali.set_console_text("test_rotary_switch_and_DIP_switch: setting rotary=%d,DIP=%d != actually rotary=%d,DIP=%d" %(expect_rotary_switch[i], expect_DIP_switch[i],((switches&0xFF00)>>8),(switches&0xFF)))
                print("test_rotary_switch_and_DIP_switch: setting rotary=%d,DIP=%d != actually rotary=%d,DIP=%d" %(expect_rotary_switch[i], expect_DIP_switch[i],((switches&0xFF00)>>8),(switches&0xFF)))
                                    
        self.set_console_instruction_text(ret_val, "Step%d: CCB rotary switch and BCD inputs test "%stepnumber)           
        self.cali.set_tutorial("tutorial.jpg")
        return ret_val 
        
    def test_usb_and_keys(self, stepnumber):     
        ret_val = 0          

        self.cali.set_instruction("1. 1)Plug the USB drive for test into the CCB.\n      将测试用的U盘插入CCB板 .\n\n    \
2)Press the MCU RESET key on CCB.\n      按下CCB板上的复位按钮.\n\n    \
3)Press the pass button on GUI to continue the test. \n      点击界面上的“Pass 通过”按钮继续测试.\
\\nFONTCOLOR=BLACK\\nFONTSIZE=16")   
        self.cali.set_tutorial("usb_keys1.jpg")     
        self.delay()
        self.cali.set_instruction("2. 1)Check for the LED status.\n    检查LED灯的状态.\n\n    \
2)IF LED solid ON ,then press Pass button on GUI, else press Fail button. \n    如果LED长亮, 请点击界面上的“Pass 通过”按钮, 否则点击界面上的“Fail 不良”按钮.\
\\nFONTCOLOR=BLACK\\nFONTSIZE=16")  
        self.cali.set_tutorial("usb_keys2.jpg")     
        self.delay()
        if self.cali.get_check_status() != 0:
            ret_val = self.FT_USB_AND_KEYS + self.SUBFT_UNEXPECTED
            self.ft_list.append(hex(ret_val).lstrip("0x"))
            print("test_usb_and_keys: LED flashes no 3 times.")
        else:    
            self.cali.set_instruction("3. 1)Plug out the USB drive, press the MCU RESET key on CCB.    拔出CCB板上的测试U盘, 并按下复位按钮 .\n\n    \
2)Wait 10 seconds.    等待10秒 .\n\n    \
3)IF four LEDs light up, then press the Pass button on GUI else press Fail button.\n      如果四个LED灯全亮, 请点击界面上的“Pass 通过”按钮, 否则点击界面上的“Fail 不良”按钮.\
\\nFONTCOLOR=BLACK\\nFONTSIZE=16")           
            self.cali.set_tutorial("usb_keys3.jpg")     
            self.delay()
            if self.cali.get_check_status() != 0:
                ret_val = self.FT_USB_AND_KEYS + self.SUBFT_UNEXPECTED
                self.ft_list.append(hex(ret_val).lstrip("0x"))
                print("test_usb_and_keys: reset fail.")
            
        self.set_console_instruction_text(ret_val, "Step%d: CCB USB and keys test "%stepnumber)            
        self.cali.set_tutorial("tutorial.jpg")
        return ret_val 
        
    def test_leds(self, stepnumber):     
        ret_val = 0          
        self.set_console_instruction_text(ret_val, "Step%d: CCB LEDs test "%stepnumber)  
        return ret_val 

    def test_ethernet(self, stepnumber):     
        ret_val = 0                  
        (ret_status, response) = self.cali.modbus_command(self.hmi_port, self.slave_id, self.cali.MB_CODE_READ, self.MB_ETHERNET_TEST_FLAG, 1)                    
        if (ret_status != self.SUBFT_MD_OK):
            ret_val = self.FT_ETHERNET + ret_status
            self.ft_list.append(hex(ret_val).lstrip("0x"))
            
        if (response != 1):
            ret_val = self.FT_ETHERNET + self.SUBFT_UNEXPECTED
            self.ft_list.append(hex(ret_val).lstrip("0x"))   
            self.cali.set_console_text("test_ethernet: the ethernet test flag = %d, not the the expect value 1." %(response))
            
        self.set_console_instruction_text(ret_val, "Step%d: CCB Ethernet test "%stepnumber)  
        return ret_val 
    
    def run(self):
        ret_val = 0          
        self.cali.ack_to_plying = 1          
        
        ret_val |= self.test_usb_and_keys(1)    
        ret_val |= self.test_hmi(2)  
        ret_val |= self.test_di(3)
        ret_val |= self.test_ai(4)
        ret_val |= self.test_fram(5)
        ret_val |= self.test_do(6)
        ret_val |= self.test_uart0(7)
        ret_val |= self.test_scada(8)
        ret_val |= self.test_ethernet(9)
        ret_val |= self.test_rotary_switch_and_DIP_switch_inputs(10)
 
        self.set_console_instruction_text(ret_val, "CCB FCT Test ")
        if (ret_val):
            print ("fault list: ", self.ft_list) 
            self.cali.set_console_text("fault list: ")   
            for fault in self.ft_list:
                self.cali.set_console_text("%s"%fault) 
            self.cali.set_tutorial("fail.jpg")   
            self.cali.set_check_status(1)
        else:
            self.cali.set_tutorial("pass.jpg")   
            self.cali.set_check_status(0)
            
        self.cali.ack_to_plying = 0   
        self.cali.fct_ccb_running = 0
        
        if (self.en_print):
            print("CCB FCT end...")
        
    