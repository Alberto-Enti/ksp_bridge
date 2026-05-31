def build_telemetry_payload(vessel, client):


    control = vessel.control
    orbit = vessel.orbit
    comms = vessel.comms
    resources = vessel.resources
    
    body = orbit.body
    ref_surface = body.reference_frame 
    ref_orbit = body.non_rotating_reference_frame


    flight_surface = vessel.flight(ref_surface)
    flight_orbit = vessel.flight(ref_orbit)

    sas = control.sas
    rcs = control.rcs
    gear = control.gear
    brakes = control.brakes
    lights = control.lights
    current_stage = control.current_stage

    has_signal = comms.can_communicate
    situation = vessel.situation

    alt_terrain = flight_surface.surface_altitude
    alt_sea_level = flight_surface.mean_altitude
    vel_surface = flight_surface.speed
    vel_h = flight_surface.horizontal_speed
    vel_v = flight_surface.vertical_speed
    g_force = flight_surface.g_force

    vel_orbit = flight_orbit.speed

    apoapsis = orbit.apoapsis_altitude
    periapsis = orbit.periapsis_altitude
    inclination = orbit.inclination
    eta_ap = orbit.time_to_apoapsis
    eta_pe = orbit.time_to_periapsis

    planet_name = body.name
    surface_gravity = body.surface_gravity
    met = vessel.met
    mass = vessel.mass
    thrust = vessel.available_thrust
    crew_count = vessel.crew_count

    ec_max = resources.max("ElectricCharge")
    mono_max = resources.max("MonoPropellant")
    fu_max = resources.max("LiquidFuel")
    ox_max = resources.max("Oxidizer")

    ec = resources.amount("ElectricCharge")
    mono = resources.amount("MonoPropellant")
    fu = resources.amount("LiquidFuel")
    ox = resources.amount("Oxidizer")

    ec_pct = (ec / ec_max) if ec_max > 0 else 0
    mono_pct = (mono / mono_max) if mono_max > 0 else 0
    fu_pct = (fu / fu_max) if fu_max > 0 else 0
    ox_pct = (ox / ox_max) if ox_max > 0 else 0

    VesselSituation = client.space_center.VesselSituation
    is_grounded = situation in (
        VesselSituation.landed, 
        VesselSituation.splashed, 
        VesselSituation.pre_launch
    )

    current_weight = mass * surface_gravity
    twr = (thrust / current_weight) if thrust > 0 else 0.0


    return {
        "sas": sas,
        "rcs": rcs,
        "com_link": has_signal,
        "landing_gear": gear,
        "brakes": brakes,
        "lights": lights,
        "grounded": is_grounded,

        "alt_terrain": alt_terrain,
        "alt_sea_level": alt_sea_level,
        "apoapsis": apoapsis,
        "periapsis": periapsis,
        "inclination": inclination,
        "eta_pe": eta_pe,
        "eta_ap": eta_ap,

        "vel_surface": vel_surface,
        "vel_orbit": vel_orbit,
        "vel_target": 0.0,
        "vel_h_component": vel_h,
        "vel_v_component": vel_v,

        "twr": twr,
        "kerbals_in_vessel": crew_count,
        "g_force": g_force,
        "time_elapsed": met,

        "electric_charge": ec_pct,
        "monoprop": mono_pct,
        "oxidizer": ox_pct,
        "liquid_fuel": fu_pct,

        "current_planet": planet_name,
        "current_stage": current_stage
    }