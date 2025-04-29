# Ensure vpython is installed: pip install vpython
from vpython import graph, gcurve, color, vector, rate, mag, norm, cross, sqrt, cos, pi, scene, sphere
import time
import math # Use math module for standard functions if needed outside vpython context

#===========================================================
# Function for the LRC Circuit Simulation (Original VPython)
#===========================================================
def simulate_lrc_circuit():
    """Simulates an LRC circuit with an AC EMF using VPython."""
    print("--- Starting LRC Circuit Simulation (VPython) ---")
    
    # Parameters
    Emf = 5
    C = 1e-4
    L = 0.2
    R = 10
    
    # Initial Conditions
    Q = C * Emf 
    I = 0
    t = 0
    dt = 0.0001
    
    # Driving Frequency
    w0 = 219 # rad/s
    
    # Natural Frequency Calculation
    # Use math.sqrt here as it's outside a vpython operation
    natural_w0 = 1 / math.sqrt(L * C) if L > 0 and C > 0 else 0
    print(f"Natural Frequency w0 = {natural_w0:.2f} rad/s")
    print(f"Driving Frequency w0 = {w0} rad/s") 

    # Setup VPython Graph
    # This will create a new graph area in the browser each time it's called
    tgraph = graph(title="LRC Circuit (Driven)", xtitle="Time [s]", ytitle="Vc [volts]",
                   width=500, height=350, x=0, y=0) # Position graph
    f1 = gcurve(color=color.blue, label="Vc")

    # Simulation Loop
    while t < 0.8:
        # Optional: Slow down the simulation rendering in the browser
        # rate(1000) 
        
        # Use math.cos as it's a standard calculation before vpython updates
        alpha = (Emf * math.cos(w0 * t) - I * R - Q / C) / L if L != 0 and C != 0 else 0
        I = I + alpha * dt
        Q = Q + I * dt 
        
        t = t + dt
        Vc = Q / C if C != 0 else 0
        f1.plot(t, Vc) # Plot to the VPython graph

    # Post-simulation calculation
    w0_calc_after = 2 * math.pi / 2.87e-2
    print(f"Post-simulation calculation: w0 = {w0_calc_after:.2f} rad/s")
    print("--- LRC Circuit Simulation Complete ---")


#===========================================================
# Function for the RC Circuit Simulation (Original VPython)
#===========================================================
def simulate_rc_circuit():
    """Simulates charging of an RC circuit with a DC EMF using VPython."""
    print("--- Starting RC Circuit Simulation (VPython) ---")
    
    # Setup VPython Graph
    # This creates another graph area
    tgraph = graph(title="RC Circuit (Charging)", xtitle="t [s]", ytitle="Vc [volts]",
                   width=450, height=300, x=0, y=400) # Position below LRC graph
    f1 = gcurve(color=color.blue, label="Vc")

    # Parameters
    Emf = 5
    R = 100
    C = 0.1
    
    # Initial Conditions
    Q = 0
    t = 0
    dt = 0.01
    t_max = 10.0 # Simulate for 10 seconds

    # Simulation Loop
    while t < t_max:
        # Optional: Slow down
        # rate(100) 
        
        dQ = dt * (Emf - Q / C) / R if R > 0 and C != 0 else 0
        Q = Q + dQ
        t = t + dt
        Vc = Q / C if C != 0 else 0
        f1.plot(t, Vc) # Plot to VPython graph
        
    rc_tau = R * C if R > 0 and C > 0 else 0
    print(f"RC Time Constant (tau) = {rc_tau:.2f} s")
    print("--- RC Circuit Simulation Complete ---")



#===========================================================
# Function for the Gravitational Orbit Simulation
#===========================================================

def simulate_orbit_3d():
    """Simulates a simple gravitational orbit using VPython (3D scene and graph)."""
    print("--- Starting Orbit Simulation (VPython) ---")

    # IMPORTANT: Clear the previous 3D scene objects if desired
    # Otherwise, new objects might overlay or add to existing ones in loops
    # scene.delete() # Deletes all objects in the main 3D scene
    # OR specifically delete objects if you track them. For simplicity,
    # let's allow overlaying or rely on VPython's default behavior for now.
    # If things look weird after the first loop, uncomment scene.delete().
    
    # Setup 3D scene implicitly, or configure scene explicitly if needed
    # scene.width = 400
    # scene.height = 300
    # scene.title = "Orbital Path"

    # Constants and Parameters
    G = 1
    M = 1 # Mass of central body
    m = 1 # Mass of orbiting body
    R_init = 1 # Initial radius (distance) - renamed from R to avoid conflict with resistance
    v0 = 0.7 # Initial speed (perpendicular to radius)

    # Create 3D Objects (These will appear in the VPython 3D scene)
    central_body = sphere(pos=vector(0,0,0), radius=0.1, color=color.red, make_trail=False)
    orbiting_body = sphere(pos=vector(R_init,0,0), radius=0.05, color=color.blue, make_trail=True, trail_type='curve', interval=10, retain=500) # Make a trail

    # Setup Graph for dA/dt
    # This creates another graph area
    g2 = graph(title="Area Sweep Rate (dA/dt)", xtitle="t", ytitle="dA/dt",
               width=400, height=200, x=550, y=0) # Position beside LRC graph
    f5 = gcurve(color=color.blue, label="dA/dt")

    # Initial Conditions using vpython.vector
    orbiting_body.pos = vector(R_init, 0, 0) # Set initial position of the 3D sphere
    p = m * vector(0, v0, 0) # Initial momentum vector
    t = 0
    dt = 0.001
    t_max = 15.0

    # Simulation Loop
    while t < t_max:
        # Control animation speed in the browser
        rate(1000) # Aim for 1000 calculations per second realtime
        
        # Use vpython functions for vector math
        r_vec = orbiting_body.pos # Get current position vector from the sphere object
        r_mag = mag(r_vec)
        
        if r_mag == 0: # Avoid division by zero
            F = vector(0,0,0)
        else:
            r_hat = norm(r_vec)
            F = -G * M * m * r_hat / r_mag**2
        
        # Update Momentum and Position (Euler-Cromer)
        p = p + F * dt
        orbiting_body.pos = orbiting_body.pos + (p / m) * dt # Update sphere's position
        
        # Calculate Area Sweep Rate
        # Use vpython.cross and vpython.mag
        dA_dt = mag(cross(orbiting_body.pos, p)) / (2 * m) if m != 0 else 0
                                           
        # Plot dA/dt to the VPython graph
        f5.plot(t, dA_dt)
        
        # Update time
        t = t + dt

    print("--- Orbit Simulation Complete ---")

def simulate_orbit():
    """Simulates a simple gravitational orbit and checks area sweep rate."""
    print("--- Starting Orbit Simulation ---")

    # Constants and Parameters
    G = 1
    M = 1 # Mass of central body
    m = 1 # Mass of orbiting body
    R = 1 # Initial radius (distance)
    v0 = 0.7 # Initial speed (perpendicular to radius)

    # Setup Graphs
    g1 = graph(title="Orbital Path", xtitle="x", ytitle="y", width=400, height=300)
    f1 = gcurve(color=color.blue, dot=True, label="Orbiting Body (m)")
    f2 = gcurve(color=color.red, dot=True, dot_radius=5, label="Central Body (M)")
    f2.plot(0, 0) # Plot central mass at origin
    # f3 = gcurve(color=color.green) # Defined but not used in original code
    # f4 = gcurve(color=color.green) # Defined but not used in original code
    
    g2 = graph(title="Area Sweep Rate (dA/dt)", xtitle="t", ytitle="dA/dt", width=400, height=200)
    f5 = gcurve(color=color.blue, label="dA/dt")

    # Initial Conditions
    r = vector(R, 0, 0)      # Initial position vector
    p = m * vector(0, v0, 0) # Initial momentum vector
    t = 0
    dt = 0.001
    
    # These variables were defined but not used in the original code
    # a = 3.57 / 2
    # b = 1.61

    # Simulation Loop
    while t < 15:
        # rate(1000) # Uncomment to slow down simulation
        
        # Calculate Gravitational Force
        r_mag = mag(r)
        r_hat = norm(r)
        F = -G * M * m * r_hat / r_mag**2
        
        # Update Momentum and Position (Euler-Cromer method)
        p = p + F * dt
        r = r + (p / m) * dt
        
        # Calculate Area Sweep Rate (dA/dt = |r x v| / 2 = |r x p| / (2m))
        dA_dt = mag(cross(r, p)) / (2 * m) # Correct dA/dt calculation
                                           # Original code had dA = ..., maybe meant dA/dt?
                                           
        # Plotting
        f1.plot(r.x, r.y)
        f5.plot(t, dA_dt)
        
        # Update time
        t = t + dt

    print("--- Orbit Simulation Complete ---")
    print("\n") # Add a newline for separation



#===========================================================
# Main Execution Loop
#===========================================================
num_loops = 3 # Number of times to cycle through the simulations

print("-----------------------------------------------------")
print("Starting VPython Simulation Loop")
print(f"Each simulation (LRC, RC, Orbit) will run {num_loops} times.")
print("Output will appear in a new browser tab.")
print("Graphs will likely be added below previous ones.")
print("Press Ctrl+C in this terminal to stop the loop.")
print("-----------------------------------------------------")
time.sleep(2) # Give user time to read message

for i in range(num_loops):
    print(f"\n======= Starting Loop Iteration {i + 1} of {num_loops} =======")
    
    # --- Run LRC Circuit ---
    print(f"\n[Iteration {i+1}] === Running LRC Circuit ===")
    try:
        simulate_lrc_circuit()
    except Exception as e:
        print(f"[Iteration {i+1}] *** ERROR in LRC Simulation: {e} ***")
    print(f"[Iteration {i+1}] === LRC Finished ===\n")
    time.sleep(2) # Pause between simulations

    # --- Run RC Circuit ---
    print(f"[Iteration {i+1}] === Running RC Circuit ===")
    try:
        simulate_rc_circuit()
    except Exception as e:
        print(f"[Iteration {i+1}] *** ERROR in RC Simulation: {e} ***")
    print(f"[Iteration {i+1}] === RC Finished ===\n")
    time.sleep(2) # Pause between simulations

    # --- Run Orbit Simulation ---
    print(f"[Iteration {i+1}] === Running Orbit Simulation ===")
    try:
        # Add a small delay before orbit sim starts allows browser maybe
        # to finish rendering previous graphs if complex.
        time.sleep(1) 
        simulate_orbit() 
        time.sleep(1) # Pause to allow rendering
        simulate_orbit_3d() # Call the 3D version

        
    except Exception as e:
        print(f"[Iteration {i+1}] *** ERROR in Orbit Simulation: {e} ***")
    print(f"[Iteration {i+1}] === Orbit Finished ===\n")
    
    print(f"======= Loop Iteration {i + 1} Complete =======")
    if i < num_loops - 1:
         print("\nPausing for 5 seconds before next iteration...")
         time.sleep(5) # Longer pause between full loops

print("\n--- All VPython simulation loops finished. ---")
print("You can now close the browser tab.")
# Add input("Press Enter to exit...") if you want the terminal to wait