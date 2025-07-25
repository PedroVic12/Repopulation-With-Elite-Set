from control import tf, step_response
import matplotlib.pyplot as plt

G = tf([1], [1, 2, 1])  # Example transfer function

t, y = step_response(G)

plt.plot(t, y)
plt.title('Step Response of G(s)')
plt.xlabel('Time (s)')
plt.ylabel('Response')

plt.grid()
plt.show()



def sinais_sistemas():
    pass