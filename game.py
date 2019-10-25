import xml.etree.ElementTree as ET

class UI:
    def getText(self):
        return input()

    def printText(self,text):
        print(text, end = "")

class user:
    def __init__(self):
        self.inventory = []

    def getInventory(self):
        return self.inventory

    def takeItem(self,item):
        self.inventory.append(item)

    def dropItem(self,item):
        self.inventory.remove(item)

    def checkInventory(self,ui):
        result = "Inventory: "
        if len(self.inventory) == 0:
            ui.printText(result + "empty\n")
        else:    
            for i in range(len(self.inventory)):
                result += self.inventory[i]
                
                # Only add comma if not last item
                if i != len(self.inventory) - 1:
                    result += ", "
            ui.printText(result + "\n")

class world:
    def __init__(self, xmlFile):
        self.roomMap = {}
        self.itemMap = {}
        self.creatureMap = {}
        self.containerMap = {}
        self.location = ""
        
        tree = ET.parse(xmlFile)
        root = tree.getroot()
        for child in root:
            if child.tag == "room":
                r = room(child);
                self.roomMap[r.getName()] = r
                if self.location == "":
                    self.location = r.getName()
            elif child.tag == "item":
                i = item(child)
                self.itemMap[i.getName()] = i;
            elif child.tag == "container":
                cont = container(child)
                self.containerMap[cont.getName()] = cont
            elif child.tag == "creature":
                creat = creature(child)
                self.creatureMap[creat.getName()] = creat

    # Accessors
    def getRoomMap(self):
        return self.roomMap;
    def getItemMap(self):
        return self.itemMap;
    def getCreatureMap(self):
        return self.creatureMap;
    def getContainerMap(self):
        return self.containerMap;
    def getLocation(self):
        return self.location;


    def changeLocation(self,command,ui):
        roomBorders = self.getRoomMap()[self.getLocation()].getInventory().getBorders()
        for border in roomBorders:
            if border.getCommand() == command:
                self.location = border.getName()
                self.roomMap[self.location].describe(ui) # Describe new room
                break;

    # Deletes all references to entity in world
    def delete(self,entity):
        if entity in self.roomMap:
            roomBorders = self.roomMap[entity].getInventory().getBorders()
            for border in roomBorders:
                neighborInventory = self.roomMap[border.getName()].getInventory()
                for neighborBorder in neighborInventory.getBorders():
                    # Delete all references to entity in neighboring rooms
                    if neighborBorder.getName() == entity:
                        neighborInventory.deleteBorder(neighborBorder)
                        
        elif entity in self.itemMap:
            for room in self.roomMap:
                self.roomMap[room].getInventory().delete(entity)
            for container in self.containerMap:
                self.containerMap[container].delete(entity)
                
        elif entity in self.containerMap or entity in self.creatureMap:
            for room in self.roomMap:
                self.roomMap[room].getInventory().delete(entity)

### Room, Borders, and Inventory #############################################################

# ADD look() command to prompt room to print description
class room:
    def __init__(self,node):
        self.name = node.find("name").text
        self.description = node.find("description").text
        self.status = ""
        self.type = "regular"
        for child in node:
            if child.tag == "type":
                self.type = child.text
            elif child.tag == "status":
                self.status = child.text
        self.inventory = inventory(node)

    # Accesor Operators
    def getName(self):
        return self.name
    def getDescription(self):
        return self.description
    def getType(self):
        return self.type
    def getStatus(self):
        return self.status
    def getInventory(self):
        return self.inventory

    def describe(self,ui):
        ui.printText(self.name + "\n\n")
        ui.printText(self.description + "\n\n")
        self.inventory.printItems(ui)            
    
# Add accessors to design
class inventory:
    def __init__(self,node):
        self.items = [] 
        self.containers = []
        self.creatures = []
        self.borders = [] 
        self.triggers = [] 
        for child in node:
            # Lists of strings
            if child.tag == "item":
                self.items.append(child.text)
            elif child.tag == "container":
                self.containers.append(child.text)
            elif child.tag == "creature":
                self.creatures.append(child.text)
            # Lists of borders/triggers
            elif child.tag == "border":
                self.borders.append(border(child))
            elif child.tag == "trigger":
                self.triggers.append(trigger(child))

    def getItems(self):
        return self.items
    def getContainers(self):
        return self.containers
    def getCreatures(self):
        return self.creatures
    def getBorders(self):
        return self.borders
    def getTriggers(self):
        return self.triggers


    def printItems(self,ui):
        result = ""
        ui.printText("You see ")
        if len(self.items) == 0:
            result = "no items"
        else:
            for i in range(len(self.items)):
                result += self.items[i]
                if i != len(self.items)-1:
                    result += ", "
        ui.printText(result + "\n")

    def addItem(self,item):
        self.items.append(item)

    # entity is either the name of a creature, item, or container, or it is a border object  
    def delete(self,entity):
        if entity in self.creatures:
            self.creatures.remove(entity)
        elif entity in self.items:
            self.items.remove(entity)
        elif entity in self.containers:
            self.containers.remove(entity)
        elif entity in self.borders:
            self.borders.remove(entity)

class border:
    def __init__(self,node):
        self.direction = node.find("direction").text
        self.name = node.find("name").text
        self.command = self.direction[0:1]

    def __eq__(self, other): 
        if not isinstance(other, border):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.direction == other.direction and self.name == other.name

    def getName(self):
        return self.name

    def getCommand(self):
        return self.command

    def getDir(self):
        return self.direction

###Items, Containers, and Creatures ############################################################

class item:
    def __init__(self,node):
        self.name = node.find("name").text
        self.writing = node.find("writing").text
        self.status = ""
        self.description = ""
        
        self.print = ""
        self.actions = [] # Contains action objects, if turned on
        self.triggers = [] # Contains trigger objects
        for child in node:
            if child.tag == "status":
                self.status = child.text
            elif child.tag == "description":
                self.description = child.text
            elif child.tag == "turnon":
                for grandkid in child:
                    if grandkid.tag == "print":
                        self.print = grandkid.text # Will there only be one?
                    else:
                        self.actions.append(action(grandkid.text)) # action object
            elif child.tag == "trigger":
                self.triggers.append(trigger(child))
                
    # Accessors
    def getName(self):
        return self.name
    def getWriting(self):
        return self.writing
    def getStatus(self):
        return self.status
    def getDescription(self):
        return self.description
    def getPrint(self):
        return self.print

    # Do we want these?
    def getActions(self):
        return self.actions
    def getTriggers(self):
        return self.triggers

### Normal Item Member Functions ##############################################
    def read(self,ui):
        if self.writing == "":
            ui.printText("Nothing written\n")
        else:
            ui.printText(self.writing + "\n")

    def turnon(self,world,ui):
        if self.actions == []:
            ui.printText("This object cannot be turned on\n")
        else:
            for action in self.actions:
                action.performAction(world)
        ui.printText(self.print + "\n")

    def changeStatusTo(self,newStatus):
        self.status = newStatus

###############################################################################

class container:
    def __init__(self,node):
        self.name = node.find("name").text
        self.status = ""
        self.items = []
        self.accepts = []
        self.triggers = []
        for child in node:
            if child.tag == "status":
                self.status = child.text
            elif child.tag == "item":
                self.items.append(child.text)
            elif child.tag == "accept":
                self.accepts.append(child.text)
            elif child.tag == "trigger":
                self.triggers.append(trigger(child))

    def getName(self):
        return self.name
    def getStatus(self):
        return self.status
    def getItems(self):
        return self.items
    def getAccepts(self):
        return self.accepts
    def getTriggers(self):
        return self.triggers             

    def open(self,ui):
        itemStr = ""
        if len(self.items) == 0: # No items
            ui.printText(self.name + " is empty\n")
            itemStr = "no items"
        else:   
            for i in range(len(self.items)):
                itemStr += self.items[i]
                if (i != len(self.items)-1):
                    itemStr += ", "
                    
        ui.printText(self.name + " contains " + itemStr + "\n")

    def deleteItem(self,itemName): 
        self.items.remove(itemName)

    def addItem(self,itemName):
        self.items.append(itemName)

    def changeStatusTo(self,newStatus):
        self.status = newStatus

    def canAccept(self,item):
        if self.accepts != []:
            if item not in self.accepts:
                return False
        return True

class creature:
    def __init__(self,node):
        self.name = node.find("name").text
        self.status = ""
        self.description = ""
        self.vulnerabilities = []
        self.triggers = []
        for child in node:
            if child.tag == "status":
                self.status = child.text
            elif child.tag == "description":
                self.description = child.text
            elif child.tag == "vulnerability":
                self.vulnerabilities.append(child.text)
            elif child.tag == "trigger":
                self.triggers.append(trigger(child))
                
            # define self.attack
            elif child.tag == "attack":
                self.attack = trigger(node.find("attack"))

    def getName(self):
        return self.name  
    def getStatus(self):
        return self.status
    def getDescription(self):
        return self.description
    def getAttack(self):
        return self.attack
    def getVulnerabilities(self):
        return self.vulnerabilities
    def getTriggers(self):
        return self.triggers
    
    def changeStatusTo(self,newStatus):
        self.status = newStatus

    def doAttack(self,world,userCommand,user,itemName,ui):
        for vulnerability in self.vulnerabilities:
            # set userCommand to "" because attack will never have command override
            if itemName == vulnerability and self.attack.conditionsMet(world,"",user):
                self.attack.initiateTrigger(world,ui)
        if itemName not in self.vulnerabilities:
            ui.printText(creature + " unfazed\n")

### Triggers and Conditions ########################################################

# Review this function batch in detail
class trigger:
    def __init__(self,node):
        self.type = "single"
        self.command = ""
        self.used = False
        self.conditions = []
        self.actions = []
        self.prints = [] # print if all conditions met
        
        # command is owner or status
        for child in node:
            if child.tag == "type":
                self.type = child.text
            elif child.tag == "command":
                self.command = child.text
            elif child.tag == "print":
                self.prints.append(child.text)

            
            elif child.tag == "action":
                self.actions.append(child.text)
            elif child.tag == "condition":
                for grandChild in child:
                    if grandChild.tag == "has":
                        self.conditions.append(owner(child))
                    elif grandChild.tag == "status":
                        self.conditions.append(status(child))

    def getPrints(self):
        return self.prints
    def getType(self):
        return self.type
    def getActions(self):
        return self.actions
    def getCommand(self):
        return self.command
    def getConditions(self):
        return self.conditions

    def conditionsMet(self,world,userCommand,user):
        for condition in self.conditions:
            if not condition.isMet(world,user) or (self.used and self.type == "single"):
                return False
            else:
                if self.command != "":
                    if userCommand != self.command:
                        return False
        return True

    # maybe include in above function
    def overridesCommand(self,world,userCommand,user):
        if self.command != "":
            if self.command == userCommand and self.conditionsMet(world,userCommand,user): 
                return True
        return False
    
    # Maybe bad function
    def initiateTrigger(self,world,ui):
        self.used = True
        for theAction in self.actions:
            # MAYBE NEEDED ELSEWHERE
            actionOb = action(theAction)
            actionOb.performAction(world)
        result = ""
        for item in self.prints:
            result += item + "\n"
        ui.printText(result)

class condition:
    def __init__(self,node):
        self.object = node.find("object").text

    # Maybe move to derived owner class
    def getObjectMap(self,world):
        if self.object in world.getItemMap():
            return world.getItemMap()
        elif self.object in world.getContainerMap():
            return world.getContainerMap()

class owner(condition):
    def __init__(self,node):
        super().__init__(node)
        self.owner = node.find("owner").text
        self.has = False
        
        if node.find("has").text == "yes":
            self.has = True

    def isMet(self,world,user):
        if self.owner == "inventory":
            ownerInventory = user.getInventory()
        else:
            ownerInventory = self.getOwnerItems(world)

        if ((self.object in ownerInventory) == self.has):
            return True
        return False

    # Check to make sure looks for proper owners
    def getOwnerItems(self,world):
        if self.owner in world.getContainerMap():
            return world.getContainerMap()[self.owner].getItems()
        elif self.owner in world.getRoomMap():
            return world.getRoomMap()[self.owner].getInventory().getItems()

class status(condition):
    def __init__(self,node):
        super().__init__(node)
        self.status = node.find("status").text

    # User not used, but meant to be identical to isMet() in owner
    def isMet(self,world,user):
        if self.getObjectMap(world)[self.object].getStatus() == self.status:
            return True
        return False

### Commands ###########################################################################

class action:
    # internal command initially a string
    def __init__(self,internalCommand):
        self.command = internalCommand.split()
        self.object = "" # Defined unless Game first word
        self.owner = "" # Only defined if Add first word
        if self.command[0] != "Game":
            self.object = self.command[1]
        if self.command[0] == "Add":
            self.owner = self.command[3]

    def performAction(self,world):
        if self.validCommand(): 
            if self.command[0] == "Add":
                self.getOwnerItems(world).append(self.object)               
            elif self.command[0] == "Delete":
                world.delete(self.object)
            elif self.command[0] == "Update":
                # Only items and containers can have statuses
                self.getObjectMap(world)[self.object].changeStatusTo(self.command[3])
            elif self.command[0] == "Game":
                # THIS is supposed to end while loop; ponder
                return "Victory!"
        
    # Checks for valid command structure
    def validCommand(self):
        if len(self.command) == 4:
            if (self.command[0] == "Add" or self.command[0] == "Update") and self.command[2] == "to":
                return True
        elif len(self.command) == 2:
            if (self.command[0] == "Delete") or (self.command[0] == ["Game","over"]):
                return True
        return False

    def getObjectMap(self,world):
        if self.object in world.getItemMap():
            return world.getItemMap()
        elif self.object in world.getContainerMap():
            return world.getContainerMap()
        elif self.object in world.getCreatureMap():
            return world.getCreatureMap()
        elif self.object in world.getRoomMap():
            return world.getRoomMap()

    def getOwnerItems(self,world):
        if self.owner in world.getContainerMap():
            return world.getContainerMap()[self.owner].getItems()
        elif self.owner in world.getRoomMap():
            return world.getRoomMap()[self.owner].getInventory().getItems()

# Returns True if command overwritten, False otherwise
def checkTriggers(command,world,user,ui):
    commandOverwritten = False
    roomInventory = world.getRoomMap()[world.getLocation()].getInventory()

    # Check room triggers
    for trigger in roomInventory.getTriggers():
        if trigger.conditionsMet(world,command,user):
            trigger.initiateTrigger(world,ui)
        if trigger.overridesCommand(world,command,user):
            commandOverwritten = True;            
            
    # Check room item triggers        
    for itemName in roomInventory.getItems():
        item = world.getItemMap()[itemName]
        for trigger in item.getTriggers():
            if trigger.conditionsMet(world,command,user):
                trigger.initiateTrigger(world,ui)
            if trigger.overridesCommand(world,command,user):
                commandOverwritten = True;
                

    # Check room container triggers      
    for containerName in roomInventory.getContainers():
        container = world.getContainerMap()[containerName]
        for trigger in container.getTriggers():
            if trigger.conditionsMet(world,command,user):
                trigger.initiateTrigger(world,ui)
            if trigger.overridesCommand(world,command,user):
                commandOverwritten = True;

    # Check room creature triggers 
    for creatureName in roomInventory.getCreatures():
        creature = world.getCreatureMap()[creatureName]
        for trigger in creature.getTriggers():
            if trigger.conditionsMet(world,command,user):
                trigger.initiateTrigger(world,ui)
            if trigger.overridesCommand(world,command,user):
                commandOverwritten = True;
                
    return commandOverwritten

def applyRules(ui,player,command,world):
    parsed = command.split()
    # See if command overridden
    if checkTriggers(command,world,player,ui):
        return;
    
    # Check Inventory
    if command == "i": 
        player.checkInventory(ui)
        
    # Change rooms
    elif (command in ['n','s','e','w']):
        oldLocation = world.getLocation()
        world.changeLocation(command,ui)
        if oldLocation == world.getLocation():
            ui.printText("Can't go that way\n")
            
    # Command has 2 words
    elif len(parsed) == 2:
        firstWord,secondWord = parsed[0],parsed[1]

        # If secondWord is an item
        if secondWord in world.getItemMap():
            item = world.getItemMap()[secondWord]

            # Take item
            if firstWord == 'take': # put item in inventory
                player.takeItem(item.getName())
                ui.printText(item.getName() + " added to inventory\n")

            # Read item
            elif firstWord == 'read':
                if item.getName() in player.getInventory():
                    item.read(ui)                    
                else:
                    ui.printText(item.getName() + " not in inventory\n")

            # Drop item
            elif firstWord == 'drop':
                roomInventory = world.getRoomMap()[world.getLocation()].getInventory()
                roomInventory.addItem(item.getName())
                player.dropItem(item.getName())
                ui.printText(item.getName() + " dropped\n")
                
            else:
                ui.printText("Invalid command\n")
        
        elif firstWord == 'open':
            roomType = world.getRoomMap()[world.getLocation()].getType()
            roomContainers = world.getRoomMap()[world.getLocation()].getInventory().getContainers()

            # Open exit
            if secondWord == "exit" and roomType == "exit":
                ui.printText("Game Over\n")
        
            # Open container
            elif secondWord in roomContainers:
                container = world.getContainerMap()[secondWord]
                container.open(ui)
                
            else:
                ui.printText("Invalid command\n")
        else:
            ui.printText("Invalid command\n")
                
    elif len(parsed) == 3:
        firstWord,secondWord,thirdWord = parsed[0],parsed[1],parsed[2]

        # Turn on item
        if firstWord == "turn" and secondWord == "on":
            if thirdWord in player.getInventory():
                item = world.getItemMap()[thirdWord] 
                ui.printText("You activate the " + item.getName() + "\n")
                item.turnon(world,ui)
                
            else:
                ui.printText(item.getName() + " not in inventory\n")
        else:
            ui.printText("Invalid command\n")
            
    elif len(parsed) == 4:
        firstWord,secondWord,thirdWord,fourthWord = parsed[0],parsed[1],parsed[2],parsed[3]
        
        # Put item in container
        if firstWord == "put" and thirdWord == "in":
            if secondWord in player.getInventory():
                itemName = secondWord
                roomContainers = world.getRoomMap()[world.getLocation()].getInventory().getContainers()
                if fourthWord in roomContainers:
                    container = world.getContainerMap()[fourthWord]
                    if container.canAccept(itemName):
                        container.addItem(itemName)
                        player.dropItem(itemName) # Edit function; HOW???
                        ui.printText("Item " + itemName + " added to " + container.getName() + "\n")
                    else:
                        ui.printText(container.getName() + " status: " + container.getStatus())
                else:
                    ui.printText(fourthWord + " not in current room\n")
            else:
                ui.printText(secondWord + " not in inventory\n")
                
        # Attack creature with item
        elif firstWord == "attack" and thirdWord == "with":
            roomCreatures = world.getRoomMap()[world.getLocation()].getInventory().getCreatures()
            if secondWord in roomCreatures:
                creature = world.getCreatureMap()[secondWord]
                if fourthWord in player.getInventory():
                    itemName = fourthWord
                    creature.doAttack(world,command,player,itemName,ui)
                else:
                    ui.printText(fourthWord + " not in inventory\n")
            else:
                ui.printText(secondWord + " not in current room\n")
        else:
            ui.printText("Invalid command\n")
    else:
        ui.printText("Invalid command\n")
        
    # Check triggers again
    checkTriggers(command,world,player,ui)

def game():
    myWorld = world("exGame.xml")
    screen = UI()
    player = user()

    myWorld.getRoomMap()[myWorld.getLocation()].describe(screen)
    while(myWorld.getRoomMap()[myWorld.getLocation()].getType() != "exit"):
        screen.printText("> ")
        command = screen.getText().lower()
        applyRules(screen,player,command,myWorld) # User inputs should be lower case
    screen.printText("Thanks for playing! ")

game()














