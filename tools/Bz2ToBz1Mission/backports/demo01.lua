-- demo01.lua
-- Near-parity Lua backport of the BZ2 demo01 gameplay states.
-- Source: demo01.cpp from the BZ2 mission DLL source drop.
--
-- Practical scope:
-- - States 10-16 are ported as closely as BZ1 Lua allows.
-- - States 0-9 still depend on IFace and DLL-era cinematic helpers, so the
--   script defaults to a "skip cinematic" playable bootstrap.

local WHITE = "white"

local STATE = {
    SETUP_UI = 0,
    INTRO_LOOP = 1,
    CONFIG_LOOP = 2,
    CLEANUP_UI = 3,
    CINEMATIC = 4,
    POST_CRASH_ANIMAL = 5,
    CAMERA_PULL = 6,
    LANDING = 7,
    SPAWN_SERVICE = 8,
    SPAWN_BIKES = 9,
    MAIN_CLEAR_PATH = 10,
    GO_TO_CRASHSITE = 11,
    RESCUE = 12,
    SCUTTLE = 13,
    GO_TO_DUSTOFF = 14,
    SUCCESS = 15,
    CLEANUP = 16,
}

local START_PLAYABLE = true
local START_COMMAND_MODE = false
local START_DIFFICULTY = 1
local ANIMAL_EAT_FALLBACK = 4.0

local NUM_SENTRIES = 1
local SENT_WAVE = 4
local NUM_FVTANKS = 1
local TANK_WAVE = 4
local NUM_FVTURRS = 9
local NUM_SQUAD1 = 2
local NUM_SQUAD2 = 2
local NUM_FRIENDS = NUM_SQUAD1 + NUM_SQUAD2
local NUM_ANIMALS = 4

local CMD_NONE = (AiCommand and AiCommand.NONE) or _G.CMD_NONE or 0
local CMD_ATTACK = (AiCommand and AiCommand.ATTACK) or _G.CMD_ATTACK or 4

mission_state = STATE.SETUP_UI
mission_command = 0
difficulty = START_DIFFICULTY

movie_playing = false
state_setup = false
turr_dead = false
first_try = true
need_target = false
sent_dead = true
tank_dead = true
service_busy = false
follow_player = true
people_rescued = false
cam_obj = true
out_of_ship = false
lost = false
timer = false
power_up_sent = false
gun_warning = false
first_strike = false
move_vehicle = false

delay_time = 0.0
delay_time2 = 0.0
max_frames = 0.0
orbit_r = 0.0
remind_time = 0.0
anim_finish_time = 0.0
sent_timer = 0
tank_timer = 0
sent_wave = 0
tank_wave = 0
sent_death_count = 0
tank_death_count = 0
current_objective = -1
counter = 0
dead_turrs = 0

player = nil
old_player = nil
player_vehicle = nil
player_killer = nil
service = nil
tug = nil
apc = nil
crashsite = nil
dropship = nil
guntow2 = nil
p1 = nil
p2 = nil
person1 = nil
person2 = nil
person3 = nil

enemy_turrs = {}
enemy_sentries = {}
enemy_tanks = {}
friend_handle = {}
active_targets = {}
animal = {}

local function is_alive(h)
    return h ~= nil and IsAlive(h)
end

local function safe_remove(h)
    if is_alive(h) then
        RemoveObject(h)
    end
end

local function safe_attack(me, him, priority)
    if not is_alive(me) or him == nil then
        return
    end
    if priority == nil then
        Attack(me, him)
    else
        Attack(me, him, priority)
    end
end

local function safe_follow(me, him, priority)
    if not is_alive(me) or him == nil then
        return
    end
    if priority == nil then
        Follow(me, him)
    else
        Follow(me, him, priority)
    end
end

local function safe_goto(me, where, priority)
    if not is_alive(me) or where == nil then
        return
    end
    if priority == nil then
        Goto(me, where)
    else
        Goto(me, where, priority)
    end
end

local function safe_stop(me, priority)
    if not is_alive(me) then
        return
    end
    if priority == nil then
        Stop(me)
    else
        Stop(me, priority)
    end
end

local function safe_set_group(h, group_id)
    if is_alive(h) and SetGroup then
        SetGroup(h, group_id)
    end
end

local function safe_set_verbose(h, value)
    if is_alive(h) and SetVerbose then
        SetVerbose(h, value)
    end
end

local function safe_look_at(h, target, priority)
    if not is_alive(h) or target == nil or not LookAt then
        return
    end
    if priority == nil then
        LookAt(h, target)
    else
        LookAt(h, target, priority)
    end
end

local function safe_set_avoid_plan(h)
    if is_alive(h) and SetAvoidType and _G.AVD_PLAN ~= nil then
        SetAvoidType(h, AVD_PLAN)
    end
end

local function safe_is_around(h)
    if h == nil then
        return false
    end
    if IsAround then
        return IsAround(h)
    end
    return is_alive(h)
end

local function start_animation(h, animation, mode, fallback_seconds)
    max_frames = 0.0
    anim_finish_time = GetTime() + (fallback_seconds or 0.0)
    if is_alive(h) and SetAnimation then
        local frames = SetAnimation(h, animation, mode or 0)
        if frames and frames > 0 then
            max_frames = frames
            anim_finish_time = 0.0
        end
    end
end

local function animation_finished(h, animation)
    if is_alive(h) and GetAnimationFrame and max_frames > 0 then
        return GetAnimationFrame(h, animation) >= (max_frames - 1)
    end
    return GetTime() >= anim_finish_time
end

local function set_named_objective(h, name)
    if is_alive(h) then
        SetObjectiveOn(h)
        SetObjectiveName(h, name)
    end
end

local function clear_and_add_objective(file_name)
    ClearObjectives()
    AddObjective(file_name, WHITE, 10)
end

function Save()
    return mission_state, mission_command, difficulty,
           movie_playing, state_setup, turr_dead, first_try, need_target,
           sent_dead, tank_dead, service_busy, follow_player, people_rescued,
           cam_obj, out_of_ship, lost, timer, power_up_sent, gun_warning,
           first_strike, move_vehicle,
           delay_time, delay_time2, max_frames, orbit_r, remind_time, anim_finish_time,
           sent_timer, tank_timer, sent_wave, tank_wave,
           sent_death_count, tank_death_count, current_objective, counter, dead_turrs,
           player, old_player, player_vehicle, player_killer,
           service, tug, apc, crashsite, dropship, guntow2,
           p1, p2, person1, person2, person3,
           enemy_turrs[1], enemy_turrs[2], enemy_turrs[3], enemy_turrs[4], enemy_turrs[5],
           enemy_turrs[6], enemy_turrs[7], enemy_turrs[8], enemy_turrs[9],
           enemy_sentries[1],
           enemy_tanks[1],
           friend_handle[1], friend_handle[2], friend_handle[3], friend_handle[4],
           active_targets[1], active_targets[2], active_targets[3], active_targets[4],
           animal[1], animal[2], animal[3], animal[4]
end

function Load(...)
    local arg = {...}
    if #arg == 0 then
        return
    end

    mission_state, mission_command, difficulty,
    movie_playing, state_setup, turr_dead, first_try, need_target,
    sent_dead, tank_dead, service_busy, follow_player, people_rescued,
    cam_obj, out_of_ship, lost, timer, power_up_sent, gun_warning,
    first_strike, move_vehicle,
    delay_time, delay_time2, max_frames, orbit_r, remind_time, anim_finish_time,
    sent_timer, tank_timer, sent_wave, tank_wave,
    sent_death_count, tank_death_count, current_objective, counter, dead_turrs,
    player, old_player, player_vehicle, player_killer,
    service, tug, apc, crashsite, dropship, guntow2,
    p1, p2, person1, person2, person3,
    enemy_turrs[1], enemy_turrs[2], enemy_turrs[3], enemy_turrs[4], enemy_turrs[5],
    enemy_turrs[6], enemy_turrs[7], enemy_turrs[8], enemy_turrs[9],
    enemy_sentries[1],
    enemy_tanks[1],
    friend_handle[1], friend_handle[2], friend_handle[3], friend_handle[4],
    active_targets[1], active_targets[2], active_targets[3], active_targets[4],
    animal[1], animal[2], animal[3], animal[4] = unpack(arg)
end

local function set_difficulty(object, level)
    if not is_alive(object) then
        return
    end

    if level == 0 then
        SetSkill(object, 0)
    elseif level == 1 then
        SetSkill(object, 1)
    else
        SetSkill(object, 3)
    end
end

local function find_turr_target()
    for i = 1, NUM_FVTURRS do
        local t = enemy_turrs[i]
        if is_alive(t) then
            local good = true
            for j = 1, NUM_FRIENDS do
                if active_targets[j] == t then
                    good = false
                    break
                end
            end
            if good then
                return t
            end
        end
    end

    for i = 1, NUM_FVTURRS do
        local t = enemy_turrs[i]
        if is_alive(t) then
            return t
        end
    end

    return nil
end

local function find_sent_target()
    for i = 1, NUM_FRIENDS do
        local h = friend_handle[i]
        if is_alive(h) then
            return h
        end
    end
    return nil
end

local function check_lose_conditions()
    if mission_state <= STATE.RESCUE and not is_alive(service) and not lost then
        ClearObjectives()
        AddObjective("demo01-L2.otf", WHITE, 5)
        FailMission(GetTime() + 10.0, "demo01-L2.otf")
        lost = true
        return
    end

    if not is_alive(tug) and not lost then
        ClearObjectives()
        AddObjective("demo01-L3.otf", WHITE, 5)
        FailMission(GetTime() + 10.0, "demo01-L3.otf")
        lost = true
    end
end

local function do_service(truck)
    for i = 1, NUM_FRIENDS do
        local h = friend_handle[i]
        if is_alive(h) and GetCurrentCommand(h) == CMD_ATTACK then
            if GetHealth(h) < 0.5 or GetAmmo(h) < 0.5 then
                safe_follow(h, player)
            end
        end
    end

    if not service_busy then
        for i = 1, NUM_FRIENDS do
            local h = friend_handle[i]
            if is_alive(h) and (GetHealth(h) < 0.5 or GetAmmo(h) < 0.5) then
                Service(truck, h)
                safe_follow(h, truck)
                current_objective = i
                service_busy = true
                follow_player = false
                break
            end
        end
    else
        if GetCurrentCommand(truck) == CMD_NONE then
            service_busy = false
            if current_objective >= 1 and is_alive(friend_handle[current_objective]) then
                safe_stop(friend_handle[current_objective])
            end
            current_objective = -1
            follow_player = true
            turr_dead = true
        end
    end

    if follow_player then
        safe_follow(truck, player)
        follow_player = false
    end
end

local function command_mortar_bikes()
    need_target = false
    for i = 1, NUM_FRIENDS do
        local h = friend_handle[i]
        if is_alive(h) then
            local cmd = GetCurrentCommand(h)
            if cmd == CMD_ATTACK then
                active_targets[i] = GetCurrentWho(h)
            elseif cmd == CMD_NONE then
                active_targets[i] = nil
                need_target = true
            end
        else
            active_targets[i] = nil
        end
    end

    local target = nil
    if is_alive(player) and is_alive(guntow2) and mission_state == STATE.GO_TO_DUSTOFF and GetDistance(player, guntow2) < 200 then
        target = guntow2
    else
        target = find_turr_target()
    end

    if need_target and target then
        for i = 1, NUM_FRIENDS do
            local h = friend_handle[i]
            if is_alive(h) and GetCurrentCommand(h) == CMD_NONE and i ~= current_objective then
                safe_attack(h, target)
                turr_dead = false
                first_try = true
                need_target = false
            end
        end
    elseif not need_target then
        first_try = true
        turr_dead = false
    end

    if not target and mission_state <= STATE.RESCUE then
        if is_alive(apc) then
            Damage(apc, 10001)
        end
        state_setup = false
        mission_state = mission_state + 1
    end
end

local function finalize_intro_transition()
    if not is_alive(tug) then
        tug = BuildObject("ivstas", 1, "spawn")
    end

    if mission_command == 0 then
        safe_follow(tug, player)
        safe_set_group(tug, -1)
        safe_set_group(service, -1)
    else
        safe_set_group(tug, 3)
        safe_follow(tug, player, 0)
        SetIndependence(tug, 1)

        safe_set_group(service, 2)
        safe_follow(service, player, 0)
        SetIndependence(service, 1)

        safe_set_group(friend_handle[1], 0)
        safe_follow(friend_handle[1], player, 0)
        SetIndependence(friend_handle[1], 1)
        safe_set_group(friend_handle[2], 0)
        safe_follow(friend_handle[2], player, 0)
        SetIndependence(friend_handle[2], 1)
        safe_set_group(friend_handle[3], 1)
        safe_follow(friend_handle[3], player, 0)
        SetIndependence(friend_handle[3], 1)
        safe_set_group(friend_handle[4], 1)
        safe_follow(friend_handle[4], player, 0)
        SetIndependence(friend_handle[4], 1)
    end

    safe_remove(crashsite)
    crashsite = BuildObject("crashdrop", 1, "crashSite")
    set_named_objective(crashsite, "Crash Site")
    set_named_objective(service, "Service Truck")
    sent_timer = 20
    tank_timer = 0
    move_vehicle = false
    CameraFinish()
    if mission_command == 0 then
        clear_and_add_objective("demo01a.otf")
    else
        clear_and_add_objective("demo01a-c.otf")
    end
end

local function spawn_playable_state()
    player = GetPlayerHandle()
    old_player = player
    if player and not IsOdf(player, "isuser") then
        player_vehicle = player
    end
    mission_command = mission_command or 0
    difficulty = difficulty or START_DIFFICULTY
    guntow2 = GetHandle("guntow2")
    if is_alive(guntow2) then
        SetSkill(guntow2, 0)
    end

    for i = 1, NUM_FVTURRS do
        enemy_turrs[i] = GetHandle(string.format("turr%d", i - 1))
        set_difficulty(enemy_turrs[i], difficulty)
    end

    if not is_alive(friend_handle[1]) then
        friend_handle[1] = BuildObject("ivmbike", 1, "spawn")
    end

    local pos = GetPosition(friend_handle[1])
    for i = 2, NUM_FRIENDS do
        if not is_alive(friend_handle[i]) then
            pos.z = pos.z + 40
            friend_handle[i] = BuildObject("ivmbike", 1, pos)
        end
    end

    if mission_command == 0 then
        safe_attack(friend_handle[1], enemy_turrs[1])
        safe_attack(friend_handle[2], enemy_turrs[1])
        safe_attack(friend_handle[3], enemy_turrs[2])
        safe_attack(friend_handle[4], enemy_turrs[2])
    else
        safe_set_group(friend_handle[1], 0)
        safe_attack(friend_handle[1], enemy_turrs[1])
        safe_set_group(friend_handle[2], 0)
        safe_attack(friend_handle[2], enemy_turrs[1])
        safe_set_group(friend_handle[3], 1)
        safe_attack(friend_handle[3], enemy_turrs[2])
        safe_set_group(friend_handle[4], 1)
        safe_attack(friend_handle[4], enemy_turrs[2])
    end

    if not is_alive(service) then
        service = BuildObject("ivserv", 1, "service")
    end

    if mission_command == 0 then
        safe_set_group(service, -1)
        safe_follow(service, player)
    else
        safe_set_group(service, 2)
        safe_follow(service, player)
    end

    pos = GetPosition(service)
    if not is_alive(tug) then
        pos.z = pos.z - 40
        tug = BuildObject("ivstas", 1, pos)
    end

    if mission_command == 0 then
        safe_follow(tug, player)
        safe_set_group(tug, -1)
    else
        safe_follow(tug, player)
        safe_set_group(tug, 3)
    end

    crashsite = BuildObject("crashdrop", 1, "crashSite")
    set_named_objective(crashsite, "Crash Site")
    set_named_objective(service, "Service Truck")
    sent_timer = 20
    tank_timer = 0
    mission_state = STATE.MAIN_CLEAR_PATH
    move_vehicle = false
    state_setup = true
    CameraFinish()
    if mission_command == 0 then
        clear_and_add_objective("demo01a.otf")
    else
        clear_and_add_objective("demo01a-c.otf")
    end
end

function SkipCin()
    spawn_playable_state()
end

function Start()
    mission_state = START_PLAYABLE and STATE.MAIN_CLEAR_PATH or STATE.SETUP_UI
    mission_command = START_COMMAND_MODE and 1 or 0
    difficulty = START_DIFFICULTY
    movie_playing = false
    state_setup = false
    turr_dead = false
    first_try = true
    need_target = false
    sent_dead = true
    tank_dead = true
    service_busy = false
    follow_player = true
    people_rescued = false
    cam_obj = true
    out_of_ship = false
    lost = false
    timer = false
    power_up_sent = false
    gun_warning = false
    first_strike = false
    move_vehicle = false
    delay_time = 0.0
    delay_time2 = 0.0
    max_frames = 0.0
    orbit_r = 0.0
    remind_time = 0.0
    anim_finish_time = 0.0
    sent_timer = 0
    tank_timer = 0
    sent_wave = 0
    tank_wave = 0
    sent_death_count = 0
    tank_death_count = 0
    current_objective = -1
    counter = 0
    dead_turrs = 0
    player = nil
    old_player = nil
    player_vehicle = nil
    player_killer = nil
    service = nil
    tug = nil
    apc = nil
    crashsite = nil
    dropship = nil
    guntow2 = nil
    p1 = nil
    p2 = nil
    person1 = nil
    person2 = nil
    person3 = nil
    for i = 1, NUM_FVTURRS do
        enemy_turrs[i] = nil
    end
    enemy_sentries[1] = nil
    enemy_tanks[1] = nil
    for i = 1, NUM_FRIENDS do
        friend_handle[i] = nil
        active_targets[i] = nil
    end
    for i = 1, NUM_ANIMALS do
        animal[i] = nil
    end
end

function AddObject(h)
    if IsOdf(h, "satchel") then
        StartCockpitTimer(30, 15, 5)
        timer = true
    end
end

function DeleteObject(h)
    if IsOdf(h, "fvturr") then
        turr_dead = true
        if mission_state == STATE.MAIN_CLEAR_PATH then
            dead_turrs = dead_turrs + 1
        end
    end

    if IsOdf(h, "fbspir") then
        turr_dead = true
    end

    if IsOdf(h, "ivmbike") then
        check_lose_conditions()
    end

    if IsOdf(h, "ivserv") then
        check_lose_conditions()
        if current_objective ~= -1 then
            turr_dead = true
            current_objective = -1
        end
    end

    if IsOdf(h, "ivtank") and mission_state >= STATE.MAIN_CLEAR_PATH and not safe_is_around(player_vehicle) then
        player_killer = BuildObject("fvtank", 2, "spawn2")
        player = GetPlayerHandle()
        safe_attack(player_killer, player)
    end

    if IsOdf(h, "ivstas") then
        check_lose_conditions()
    end

    if IsOdf(h, "fvsent") then
        if sent_death_count < NUM_SENTRIES then
            sent_death_count = sent_death_count + 1
        end
        if sent_death_count == NUM_SENTRIES and sent_wave < SENT_WAVE and player and GetDistance(player, "spawn2") > 75.0 then
            sent_dead = true
            sent_death_count = 0
            sent_timer = 600
            sent_wave = sent_wave + 1
        end
    end

    if IsOdf(h, "fvtank") then
        if tank_death_count < NUM_FVTANKS then
            tank_death_count = tank_death_count + 1
        end
        if tank_death_count == NUM_FVTANKS and tank_wave < TANK_WAVE and player and GetDistance(player, "spawn2") > 75.0 then
            tank_dead = true
            tank_death_count = 0
            tank_timer = 500
            tank_wave = tank_wave + 1
        end
    end
end

local function spawn_enemy_sentries()
    if sent_timer > 0 then
        sent_timer = sent_timer - 1
        return
    end

    if sent_dead then
        for i = 1, NUM_SENTRIES do
            enemy_sentries[i] = BuildObject("fvsent", 2, "spawn2")
            safe_attack(enemy_sentries[i], player, 0)
            set_difficulty(enemy_sentries[i], difficulty)
        end
        sent_dead = false
    end
end

local function spawn_enemy_tanks()
    if tank_timer > 0 then
        tank_timer = tank_timer - 1
        return
    end

    if tank_dead then
        for i = 1, NUM_FVTANKS do
            enemy_tanks[i] = BuildObject("fvtank", 2, "spawn2")
            safe_attack(enemy_tanks[i], is_alive(service) and service or player, 0)
            set_difficulty(enemy_tanks[i], difficulty)
        end
        tank_dead = false
    end
end

local function maybe_spawn_supplies(apc_path, cleanup_target, repair_offset)
    if not is_alive(player) then
        return
    end

    if GetHealth(player) < 0.7 or GetAmmo(player) < 0.5 then
        if not is_alive(apc) and not is_alive(p1) and not is_alive(p2) then
            apc = BuildObject("ivapc", 1, apc_path)
            safe_goto(apc, apc_path)
            set_named_objective(apc, "Supply Ship")
            power_up_sent = true
        end

        if power_up_sent and is_alive(apc) and GetDistance(player, apc) < 150 then
            local pos = GetPosition(apc)
            p1 = BuildObject("apammo", 1, pos)
            pos.x = pos.x + repair_offset
            p2 = BuildObject("aprepa", 1, pos)
            SetObjectiveOff(apc)
            set_named_objective(p2, "Supplies")
            power_up_sent = false
        end
    end

    if is_alive(apc) then
        local reached_cleanup = cleanup_target ~= nil and GetDistance(apc, cleanup_target) < 175
        if ((not power_up_sent) or reached_cleanup) and (GetDistance(apc, player) > 175 or reached_cleanup) then
            safe_remove(apc)
            apc = nil
        end
    end
end

local function update_state_10()
    maybe_spawn_supplies("apc1", "spawn", 4)

    if player ~= old_player and mission_command == 0 then
        old_player = player
        safe_follow(tug, player)
    end

    if is_alive(service) and GetHealth(service) < 0.7 then
        AddHealth(service, 10)
    end

    if move_vehicle then
        finalize_intro_transition()
        return
    end

    if mission_command == 0 then
        if turr_dead and not first_try then
            command_mortar_bikes()
        end
        if first_try and turr_dead then
            first_try = false
        end
    end

    spawn_enemy_sentries()
    spawn_enemy_tanks()

    if mission_command ~= 0 and dead_turrs == 9 then
        mission_state = mission_state + 1
    end

    if is_alive(service) and mission_command == 0 then
        do_service(service)
    end
end

local function update_state_11()
    if not state_setup then
        clear_and_add_objective("demo01b.otf")
        animal[4] = BuildObject("jak_kill", 0, "animal3")
        orbit_r = 0.2
        state_setup = true
        remind_time = GetTime() + 40.0
    end

    if remind_time < GetTime() then
        if not first_strike then
            clear_and_add_objective("demo01b.otf")
            first_strike = true
            remind_time = GetTime() + 60.0
        else
            FailMission(5, "demo01_L4")
        end
    elseif state_setup and is_alive(crashsite) and GetDistance(player, crashsite) < 200.0 then
        safe_remove(enemy_sentries[1])
        state_setup = false
        person1 = BuildObject("ispilo", 1, "animal0")
        safe_goto(person1, "crashSite")
        start_animation(animal[4], "eat1", 0, ANIMAL_EAT_FALLBACK)
        AudioMessage("bz2dem01b.wav")
        CameraReady()
        CameraObject(animal[4], 3 * math.cos(orbit_r), 0.5, 3 * math.sin(orbit_r), animal[4])
        orbit_r = orbit_r + 0.015
        mission_state = mission_state + 1
    end

    if player ~= old_player then
        old_player = player
        if player and IsOdf(player, "isuser") then
            safe_attack(animal[2], player)
            safe_attack(animal[3], player)
            safe_attack(animal[4], player)
        end
    end

    if is_alive(service) and mission_command == 0 then
        do_service(service)
    end
end

local function update_state_12()
    if not state_setup then
        if not animation_finished(animal[4], "eat1") then
            CameraObject(animal[4], 3 * math.sin(orbit_r), 0.5, 3 * math.cos(orbit_r), animal[4])
            orbit_r = orbit_r + 0.015
        else
            CameraFinish()
            if mission_command == 0 then
                safe_stop(tug)
                safe_look_at(tug, crashsite)
            else
                safe_stop(tug, 0)
                safe_look_at(tug, crashsite, 0)
            end
            safe_remove(person1)
            person1 = nil
            AudioMessage("command9.wav")
            clear_and_add_objective("demo01e.otf")
            state_setup = true
            safe_remove(animal[4])
            animal[4] = BuildObject("mcjak01", 2, "animal4")
            safe_attack(animal[4], player)
            animal[2] = BuildObject("mcjak01", 2, "animal1")
            safe_attack(animal[2], player)
            animal[3] = BuildObject("mcjak01", 2, "animal2")
            safe_attack(animal[3], player)
            movie_playing = false
            remind_time = GetTime() + 40.0
            first_strike = false
        end
        return
    end

    if not movie_playing then
        if remind_time < GetTime() then
            if not first_strike then
                clear_and_add_objective("demo01e.otf")
                first_strike = true
                remind_time = GetTime() + 60.0
            else
                FailMission(5, "demo01_L5")
            end
        end

        people_rescued = true
        movie_playing = true
        for i = 1, NUM_ANIMALS do
            if is_alive(animal[i]) then
                people_rescued = false
                movie_playing = false
                cam_obj = false
                break
            end
        end

        if people_rescued then
            AudioMessage("apc2.wav")
            SetPosition(tug, "animal3")
            safe_goto(tug, "animal3")
            delay_time2 = GetTime() + 2
            return
        end
    end

    if people_rescued and GetTime() > delay_time2 and movie_playing then
        if not cam_obj then
            local pos = GetPosition(crashsite)
            SetPosition(player, "animal2")
            if is_alive(service) then
                SetPosition(service, "spawn2")
            end
            person1 = BuildObject("ispilo", 1, pos)
            safe_goto(person1, tug)
            pos.x = pos.x + 5
            person2 = BuildObject("ispilo", 1, pos)
            safe_goto(person2, tug)
            pos.z = pos.z + 5
            person3 = BuildObject("ispilo", 1, pos)
            safe_goto(person3, tug)
            cam_obj = true
            orbit_r = 1.0
            counter = 0
        else
            if counter == 2 then
                safe_remove(crashsite)
                crashsite = BuildObject("crashdrop2", 1, "crashSite")
                CameraReady()
                CameraObject(tug, 10 * math.sin(orbit_r), 4.0, 10 * math.cos(orbit_r), tug)
                safe_stop(tug)
                orbit_r = orbit_r + 0.01
            end

            if counter < 3 then
                counter = counter + 1
                delay_time = GetTime() + 5
            elseif counter < 50 then
                CameraObject(tug, 10 * math.sin(orbit_r), 4.0, 10 * math.cos(orbit_r), tug)
                orbit_r = orbit_r + 0.01
                counter = counter + 1
                delay_time = GetTime() + 5
            elseif counter < 90 then
                CameraObject(person1, 4.0, 2.0, 4.0, person1)
                orbit_r = orbit_r + 0.01
                counter = counter + 1
                delay_time = GetTime() + 5
            else
                CameraObject(tug, 10 * math.sin(orbit_r), 4.0, 10 * math.cos(orbit_r), tug)
                orbit_r = orbit_r + 0.01
                counter = counter + 1
            end

            if (is_alive(person1) and GetDistance(person1, tug) < 20) or GetTime() > delay_time then
                safe_remove(person1)
                safe_remove(person2)
                safe_remove(person3)
                person1 = nil
                person2 = nil
                person3 = nil
                CameraFinish()
                safe_remove(crashsite)
                crashsite = BuildObject("crashdrop", 1, "crashSite")
                state_setup = false
                movie_playing = false
                AudioMessage("apc3.wav")
                AudioMessage("command10.wav")
                clear_and_add_objective("demo01d.otf")
                mission_state = mission_state + 1
                safe_set_avoid_plan(tug)
                if mission_command == 0 then
                    safe_goto(tug, "spawn2")
                else
                    safe_goto(tug, "spawn2", 0)
                end
                animal[2] = BuildObject("mcjak01", 0, "animal1")
                safe_attack(animal[2], player)
            end
        end
    end

    if player ~= old_player then
        old_player = player
        if player and IsOdf(player, "isuser") then
            safe_attack(animal[2], player)
            safe_attack(animal[3], player)
            safe_attack(animal[4], player)
        end
    end
end

local function update_state_13()
    if player ~= old_player then
        old_player = player
        safe_attack(animal[2], player)
    end

    if not is_alive(crashsite) then
        dropship = BuildObject("ivdrop2", 1, "dustoff")
        AudioMessage("command8.wav")
        clear_and_add_objective("demo01c.otf")
        if crashsite ~= nil then
            SetObjectiveOff(crashsite)
        end
        if service ~= nil then
            SetObjectiveOff(service)
        end
        set_named_objective(dropship, "Dust Off")
        set_named_objective(tug, "Transport")
        state_setup = false
        delay_time = GetTime() + 7
        mission_state = mission_state + 1
        if mission_command == 0 then
            safe_follow(tug, player)
        else
            safe_follow(tug, player, 0)
        end
    end
end

local function update_state_14()
    maybe_spawn_supplies("apc2", "apcend", 2)

    if not is_alive(enemy_sentries[1]) and not is_alive(enemy_tanks[1]) and is_alive(guntow2) and not gun_warning then
        AudioMessage("command11.wav")
        gun_warning = true
    end

    if not state_setup then
        enemy_sentries[1] = BuildObject("fvsent", 2, "spawn3")
        safe_attack(enemy_sentries[1], tug)
        set_difficulty(enemy_sentries[1], difficulty)
        enemy_tanks[1] = BuildObject("fvarch", 2, "spawn4")
        safe_attack(enemy_tanks[1], player)
        set_difficulty(enemy_tanks[1], difficulty)
        old_player = player
        for i = 9, 14 do
            enemy_turrs[i - 8] = GetHandle(string.format("turr%d", i))
            set_difficulty(enemy_turrs[i - 8], difficulty)
        end
        turr_dead = true
        first_try = false
        state_setup = true
        if mission_command == 0 then
            safe_follow(tug, player)
        else
            safe_follow(tug, player, 0)
        end
    elseif mission_command == 0 then
        if turr_dead and not first_try then
            command_mortar_bikes()
        end
        if first_try and turr_dead then
            first_try = false
        end
    end

    if player ~= old_player then
        old_player = player
        safe_attack(enemy_tanks[1], player)
        if mission_command == 0 then
            safe_follow(tug, player)
        end
    end

    if is_alive(player) and is_alive(dropship) and GetDistance(player, dropship) < 100 then
        mission_state = mission_state + 1
        CameraReady()
        delay_time = GetTime() + 4
        orbit_r = 0
    end

    if is_alive(service) and mission_command == 0 then
        do_service(service)
    end
end

local function update_state_15()
    if delay_time > GetTime() and is_alive(dropship) then
        CameraObject(dropship, 50 * math.sin(orbit_r), 1 + (orbit_r * 50), 50 * math.cos(orbit_r), dropship)
        orbit_r = orbit_r + 0.01
    else
        SucceedMission(GetTime() + 5.0, "demo01-W1.otf")
        mission_state = mission_state + 1
        AudioMessage("command12.wav")
    end
end

function Update()
    if lost then
        return
    end

    player = GetPlayerHandle()

    if mission_state >= STATE.MAIN_CLEAR_PATH and player then
        if IsOdf(player, "isuser") then
            if not out_of_ship then
                GiveWeapon(player, "igsatc")
            end
            out_of_ship = true
        else
            out_of_ship = false
            player_vehicle = player
        end
    end

    if timer and GetCockpitTimer() == 0.0 then
        StopCockpitTimer()
        HideCockpitTimer()
        timer = false
    end

    if mission_state == STATE.MAIN_CLEAR_PATH and not state_setup then
        spawn_playable_state()
    elseif mission_state == STATE.MAIN_CLEAR_PATH then
        update_state_10()
    elseif mission_state == STATE.GO_TO_CRASHSITE then
        update_state_11()
    elseif mission_state == STATE.RESCUE then
        update_state_12()
    elseif mission_state == STATE.SCUTTLE then
        update_state_13()
    elseif mission_state == STATE.GO_TO_DUSTOFF then
        update_state_14()
    elseif mission_state == STATE.SUCCESS then
        update_state_15()
    elseif START_PLAYABLE then
        spawn_playable_state()
    end

    check_lose_conditions()
end
