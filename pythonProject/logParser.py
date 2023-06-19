from collections import defaultdict
# Define path to the log files you want to parse
logPath = "uvm_test_top.env.rvfi_agent.trn.log"#"/home/giorgis/project/core-v-verif/cv32e40x/sim/uvmt/vsim_results/default/hello-world/0/uvm_test_top.env.rvfi_agent.trn.log"
branchInstrsPath = "branchInstrs.rvfi_agent.trn.log"
    #"/home/giorgis/project/branchPredictionModel/files/branchInstrs.rvfi_agent.trn.log"

takenBranchPath    = "takenBranchPath.rvfi_agent.trn.log"
notTakenBranchPAth = "notTakenBranchPAth.rvfi_agent.trn.log"

size = 100
newLogPath = "new_uvm_test_top.env.rvfi_agent.trn.log"

class model:
    # Initialize the paths
    def __init__(self, logPath, branchInstrsPath, newLogPath, size):
        self.logPath = logPath
        self.branchInstrsPath = branchInstrsPath
        self.newLogPath = newLogPath

        self.number_of_instructions = 0
        self.number_of_clkCyc_pre_prediction = 0

        self.number_of_brnch_instr = 0
        self.number_taken     = 0
        self.number_not_taken = 0

        self.number_of_mispredict_pre_prediction = 0
        self.mispred_clk_cyc_penalty_pre_prediction = 0

        self.fraction_mispredict_branch_pre_prediction = 0
        self.fraction_mispredict_penalty_cyc = 0

        self.cpi_pre_prediction = 0

        self.number_of_clkCyc_perfect_prediction = 0
        self.cpi_perfect_prediction = 0

        self.number_of_clkCyc_brnach_prediction = 0
        self.cpi_brnach_prediction = 0

        self.BTB = {}
        self.access_hist_list = []
        self.BTB_size = size
        self.prediction = 3

        self.prediction_reward        = 0
        self.num_correct_prediction   = 0
        self.num_incorrect_prediction = 0


############################################################################################################################3

        self.instr_strtIndex = 0 # this is accurate
        self.instr_endIndex  = 0 # this is accurate

        self.cycle_strtIndex = 0 # = self.cycle_endIndex - size(cycle)
        self.cycle_endIndex  = 0 # this is accurate

        self.order_strtIndex = 0
        self.order_endIndex  = 0

        self.notTakenBranchDelay_dict = {}
        self.takenBranchDelay_dict    = {}

        self.notTakenBranchOrder_dict = {}
        self.takenBranchOrder_dict    = {}

        self.notTakenBranch_instr_name_dict = defaultdict(set)
        self.takenBranch_instr_name_dict    = defaultdict(set)

        print("\nClass object has been created\n")

    # Selects branch instructions from the log File and saves them into separate file
    # @param:  none
    # #return: number of branch instructions
    def read_branch_instrs(self):

        print("Reading log file from "+self.logPath)
        print("Storing Branch Instructions in "+self.branchInstrsPath + "\n")

        with open(self.logPath, "r") as logFile_ptr,  open(self.branchInstrsPath, "w") as branchInstrsFile_ptr:

            for i in range(3):
                first_3_lines = logFile_ptr.readline()
                branchInstrsFile_ptr.writelines(first_3_lines)
            print("Finished copying "+ str(i+1) + " header lines\n")
            i = 0

            for line in logFile_ptr.readlines():
                self.number_of_instructions += 1
                if ("e3 | M |" in line) or ("63 | M |" in line):
                    branchInstrsFile_ptr.writelines(line)
                    i = i+1
            self.number_of_brnch_instr = i
            print(str(self.number_of_instructions) + " instructions detected")
            print(str(self.number_of_brnch_instr) + " Branch instructions were detected\n")
            return self.number_of_brnch_instr

    def distinguish_Taken_NotTaken_branches(self):
         with open(self.logPath, "r") as logFile_ptr, open(takenBranchPath, "w") as logTakenBranch_ptr, open(notTakenBranchPAth, "w") as logNotTakenBranch_ptr :
            second_line = logFile_ptr.readline()
            second_line = logFile_ptr.readline()

            instr_strtIndex = second_line.index("      PC |")
            instr_endIndex  = instr_strtIndex + 8

            self.instr_strtIndex = instr_strtIndex
            self.instr_endIndex  = instr_endIndex

            cycle_strtIndex = second_line.index("    CYCLE |")
            cycle_endIndex  = second_line.index(" |  ORDER |")

            self.cycle_strtIndex = cycle_strtIndex
            self.cycle_endIndex  = cycle_endIndex

            order_strtIndex = second_line.index("  ORDER |")
            order_endIndex  = second_line.index(" |       PC |")

            self.order_strtIndex = order_strtIndex
            self.order_endIndex  = order_endIndex

            logNotTakenBranch_ptr.writelines(second_line)
            logTakenBranch_ptr.writelines(second_line)

            branch_line = ""
            i = 0
            last_read_line = second_line
            for line in logFile_ptr.readlines():
                last_read_line = line
                if i < 2:
                    if i == 1:
                        first_instr_finish_clkCyc = int(line[cycle_strtIndex:cycle_endIndex])
                    i += 1

                if branch_line != "":
                    instr_name_strtIndex = line.index(".c")

                    tmp_str = line[instr_name_strtIndex:len(line)]

                    instr_name_strtIndex = tmp_str.index("-")+2
                    instr_name_endIndex  = tmp_str.index("x")

                    instr_name = tmp_str[instr_name_strtIndex:instr_name_endIndex]

                    diff_currPC_prevPC = int(line[instr_strtIndex:instr_endIndex], 16) - int(branch_line[instr_strtIndex:instr_endIndex], 16)

                    cycle_diff = int(line[cycle_strtIndex:cycle_endIndex]) - int(branch_line[cycle_strtIndex:cycle_endIndex])
                    order = int(line[order_strtIndex:order_endIndex])

                    if diff_currPC_prevPC == 4: # not taken

                        if(cycle_diff in self.notTakenBranchDelay_dict):
                            self.notTakenBranchDelay_dict[cycle_diff] += 1
                            self.notTakenBranchOrder_dict[cycle_diff].append(order)

                            self.notTakenBranch_instr_name_dict[cycle_diff].add(instr_name)
                        else:
                            self.notTakenBranchDelay_dict[cycle_diff] = 1
                            self.notTakenBranchOrder_dict[cycle_diff] = []
                            self.notTakenBranchOrder_dict[cycle_diff].append(order)

                            self.notTakenBranch_instr_name_dict[cycle_diff].add(instr_name)

                        self.number_not_taken = self.number_not_taken + 1
                        logNotTakenBranch_ptr.writelines(branch_line)
                        logNotTakenBranch_ptr.writelines(line)
                        logNotTakenBranch_ptr.writelines(second_line)
                    else: # Taken

                        if(cycle_diff in self.takenBranchDelay_dict):
                            self.takenBranchDelay_dict[cycle_diff] += 1
                            self.takenBranchOrder_dict[cycle_diff].append(order)

                            self.takenBranch_instr_name_dict[cycle_diff].add(instr_name)
                        else:
                            self.takenBranchDelay_dict[cycle_diff] = 1
                            self.takenBranchOrder_dict[cycle_diff] = []
                            self.takenBranchOrder_dict[cycle_diff].append(order)

                            self.takenBranch_instr_name_dict[cycle_diff].add(instr_name)

                        self.number_taken = self.number_taken + 1
                        logTakenBranch_ptr.writelines(branch_line)
                        logTakenBranch_ptr.writelines(line)
                        logTakenBranch_ptr.writelines(second_line)

                if ("e3 | M |" in line) or ("63 | M |" in line):
                    branch_line = line
                else:
                     branch_line = ""

            self.number_of_mispredict_pre_prediction = self.number_taken
            self.mispred_clk_cyc_penalty_pre_prediction = self.number_of_mispredict_pre_prediction * 2

            last_instr_finish_clkCyc = int(last_read_line[cycle_strtIndex:cycle_endIndex])
            self.number_of_clkCyc_pre_prediction = last_instr_finish_clkCyc - first_instr_finish_clkCyc + 1

    def getPC(self, line): #TEST it
        return int(line[self.instr_strtIndex:self.instr_endIndex], 16)

    def is_branch(self, line): #TEST it
        if ("e3 | M |" in line) or ("63 | M |" in line):
            return True
        else:
            return False

    def add_to_BTB(self, pc, line):
        ind = line.index("3 | M |")
        instr = int(line[ind-7:ind+1], 16)

        nxt_pc = (instr >> 8) & 15 # nxt_pc = imm[4:1]

        tmp = (instr >> 25) & 63 # tmp = imm[10:5]

        nxt_pc = nxt_pc + (tmp << 4) # nxt_pc = imm[10:1]

        tmp = (instr >> 7) & 1  # tmp = imm[11]

        nxt_pc = nxt_pc + (tmp << 10)  # nxt_pc = imm[11:1]

        tmp = (instr >> 31) & 1  # tmp = imm[12]

        nxt_pc = nxt_pc + (tmp << 11)  # nxt_pc = imm[12:1]

        if tmp == 1: # offset is negative
            nxt_pc = 0 - nxt_pc

        nxt_pc += pc

        num_BTB_entries = len(self.BTB.keys())

        if(num_BTB_entries < self.BTB_size): # BTB is not full
            self.BTB[pc] = [nxt_pc, 3]
        else:
            self.access_hist_list.remove(self.access_hist_list[0])
            self.access_hist_list.append(pc)

    def update_BTB(self, pc, line):
        self.add_to_BTB(self, pc, line)

    def prediction_algorithm(self, pc, current_line, next_line):

        prediction = self.BTB[pc][1] > 1 # True -> branch is predicted to be taken

        diff_currPC_prevPC = int(next_line[self.instr_strtIndex:self.instr_endIndex], 16) \
                             - int(current_line[self.instr_strtIndex:self.instr_endIndex], 16)

        was_taken = diff_currPC_prevPC != 4

        if prediction:      # predicted to be take
            if was_taken:   # correctly predicted
                self.prediction_reward -= 2
            else:           # incorrectly predicted
                self.prediction_reward += 2

        if prediction == was_taken:  # correct prediction
            self.num_correct_prediction += 1
            if prediction:
                self.BTB[pc][1] = min(3, self.BTB[pc][1] + 1)
            else:
                self.BTB[pc][1] = max(0, self.BTB[pc][1] - 1)
        else:                        # incorrect prediction
            self.num_incorrect_prediction += 1
            if prediction:
                self.BTB[pc][1] = max(0, self.BTB[pc][1] - 1)
            else:
                self.BTB[pc][1] = min(3, self.BTB[pc][1] + 1)

    def branch_prediction_model(self):
        with open(self.logPath, "r") as logFile_ptr, open(self.newLogPath, "w") as newLogFile_ptr:

            for i in range(3):
                first_3_lines = logFile_ptr.readline()
                newLogFile_ptr.writelines(first_3_lines)

            current_line = logFile_ptr.readline()

            first_instr_finish_clkCyc = int(current_line[self.cycle_strtIndex:self.cycle_endIndex])

            for next_line in logFile_ptr.readlines():
                pc = self.getPC(current_line)

                cycle = int(current_line[self.cycle_strtIndex : self.cycle_endIndex])

                cycle = cycle + self.prediction_reward

                cycle = str(cycle)

                current_line[self.cycle_endIndex - len(cycle): self.cycle_endIndex] = cycle

                newLogFile_ptr.writelines(current_line)

                if pc in self.BTB.keys(): # PC is     in BTB
                    self.prediction_algorithm(pc, current_line, next_line)
                else:                     # PC is not in BTB
                    if self.is_branch(current_line): # if this instr is new branch
                        self.add_to_BTB(pc, current_line)


                current_line = next_line

            cycle = int(current_line[self.cycle_strtIndex: self.cycle_endIndex])

            cycle = cycle + self.prediction_reward

            self.number_of_clkCyc_brnach_prediction = cycle - first_instr_finish_clkCyc + 1

            cycle = str(cycle)

            current_line[self.cycle_endIndex - len(cycle): self.cycle_endIndex] = cycle

            newLogFile_ptr.writelines(current_line)


    def generate_statistics(self):
        self.read_branch_instrs()
        self.distinguish_Taken_NotTaken_branches()

        print("\n---------------------------------------------------------------")
        print("STATISTICS BEFORE BRANCH PREDICTION\n")

        print("Number of Instructions: " + str(self.number_of_instructions))
        print("Number of clock cycles: " + str(self.number_of_clkCyc_pre_prediction))
        self.cpi_pre_prediction = self.number_of_clkCyc_pre_prediction/self.number_of_instructions
        print("\nCPI without Branch Prediction: " + str(self.cpi_pre_prediction))

        print("\nNumber of Branch Instructions: " + str(self.number_of_brnch_instr))
        print("Number of CORRECTLY   predicted Branch Instructions: " + str(self.number_not_taken))
        print("Number of INCORRECTLY predicted Branch Instructions: " + str(self.number_of_mispredict_pre_prediction))
        print("\nNumber of branch misprediction penalty  (in cycles): " + str(self.mispred_clk_cyc_penalty_pre_prediction))

        self.fraction_mispredict_branch_pre_prediction = 100 * self.number_of_mispredict_pre_prediction/self.number_of_brnch_instr
        print("\nMispredicted branch instructions  (%): " + str(self.fraction_mispredict_branch_pre_prediction))

        self.fraction_mispredict_penalty_cyc = 100 * self.mispred_clk_cyc_penalty_pre_prediction/self.number_of_clkCyc_pre_prediction
        print("Branch misprediction penalty      (%): " + str(self.fraction_mispredict_penalty_cyc))
        print("---------------------------------------------------------------")
        print("\n---------------------------------------------------------------")

        print("STATISTICS WITH PERFECT BRANCH PREDICTION")

        self.number_of_clkCyc_perfect_prediction = self.number_of_clkCyc_pre_prediction - self.mispred_clk_cyc_penalty_pre_prediction
        print("\nNumber of clock cycles with perfect prediction: " + str(self.number_of_clkCyc_perfect_prediction))

        improvement = 100 * (self.number_of_clkCyc_pre_prediction - self.number_of_clkCyc_perfect_prediction)/self.number_of_clkCyc_pre_prediction
        print("Improvement compared to without prediction (%): " + str(improvement))

        self.cpi_perfect_prediction = self.number_of_clkCyc_perfect_prediction/self.number_of_instructions
        print("\nCPI with perfect prediction: " + str(self.cpi_perfect_prediction))

        improvement = 100 * (self.cpi_pre_prediction - self.cpi_perfect_prediction)/self.cpi_pre_prediction
        print("Improvement compared to without prediction (%): " + str(improvement))

        print("---------------------------------------------------------------")
        print("\n---------------------------------------------------------------")

        print("STATISTICS WITH 2-BIT BRANCH PREDICTION")

        print("\nNumber of clock cycles with 2-bit branch prediction: " + str(self.number_of_clkCyc_brnach_prediction))


        improvement = 100 * (self.number_of_clkCyc_pre_prediction - self.number_of_clkCyc_brnach_prediction)/self.number_of_clkCyc_pre_prediction
        print("Improvement compared to without prediction (%): " + str(improvement))

        self.cpi_brnach_prediction = self.number_of_clkCyc_brnach_prediction/self.number_of_instructions
        print("\nCPI with perfect prediction: " + str(self.cpi_brnach_prediction))

        improvement = 100 * (self.cpi_pre_prediction - self.cpi_brnach_prediction)/self.cpi_pre_prediction
        print("Improvement compared to without prediction (%): " + str(improvement))

        print("---------------------------------------------------------------")
        print("\n---------------------------------------------------------------")



obj = model(logPath,branchInstrsPath, newLogPath, size)

obj.generate_statistics()

# num = "   5 "

# print(int(num))
