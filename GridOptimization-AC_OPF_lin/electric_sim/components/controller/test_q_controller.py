import numpy as np

from components.controller.q_controller import QOfP, QOfU, ConstCosPhi, CosPhiOfP


def main() -> None:
    q_of_p = QOfP(p_nom_kw=100)
    q_of_u = QOfU(p_nom_kw=100)
    const_cos_phi = ConstCosPhi(p_nom_kw=100)
    cos_phi_of_p = CosPhiOfP(p_nom_kw=100)
    print(f"{q_of_p.reactive_power_kvar(-100)}")  # 48.43 -> correct
    print(f"{q_of_u.reactive_power_kvar(1.5)}")  # 10.83 -> incorrect
    print(f"{cos_phi_of_p.reactive_power_kvar(-100)}")  # 43.58 -> incorrect
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 1, figsize=(8, 12), tight_layout=True)

    voltages_pu = np.linspace(0.8, 1.2, 500)
    powers_kw = np.linspace(-100, 100, 101)

    axes[0].plot(voltages_pu, q_of_u.reactive_power_kvar(voltages_pu))
    axes[0].set_xlabel("U / p.u.")
    axes[0].set_ylabel("Q / kvar")
    axes[0].set_title("Q of U")
    axes[1].plot(powers_kw, q_of_p.reactive_power_kvar(powers_kw))
    axes[1].set_xlabel("P / kW")
    axes[1].set_ylabel("Q / kvar")
    axes[1].set_title("Q of P/ Const Cos Phi")
    axes[2].plot(powers_kw, cos_phi_of_p.reactive_power_kvar(powers_kw))
    axes[2].set_xlabel("P / kW")
    axes[2].set_ylabel("Q / kvar")
    axes[2].set_title("Cos Phi of P")
    plt.show()


if __name__ == '__main__':
    main()
