from bip_utils import (
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip39MnemonicGenerator,
)
import threading
import time

stop_thread = False
counter_lock = threading.Lock()
iteration_counter = 0
count_speed = False


def listen_for_stop():
    global stop_thread
    while not stop_thread:
        user_input = input()
        if user_input.strip().lower() == "stop":
            stop_thread = True
            print("Stopping script...")
        if user_input.strip().lower() == "speed":
            display_speed()


def display_speed():
    global iteration_counter
    global count_speed

    iteration_counter = 0
    count_speed = True
    time.sleep(1)
    with counter_lock:
        speed = iteration_counter
        count_speed = False
        iteration_counter = 0
    print(f"\rSpeed: {speed} addr/s\n", end="")


def worker_thread(addresses, lock):
    global iteration_counter
    try:
        while not stop_thread:
            mnemonic_phrase = Bip39MnemonicGenerator().FromWordsNumber(12)
            # Генеруємо адресу для кожної фрази
            # Генеруємо seed з BIP39 фрази
            seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()

            # Генеруємо ключі для Solana (BIP44)
            bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
            bip44_acc_ctx = (
                bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            )
            # Публічний ключ
            solana_address = bip44_acc_ctx.PublicKey().ToAddress()

            if solana_address in addresses:
                # Отримуємо першу адресу
                private_key = (
                    bip44_acc_ctx.PrivateKey().Raw().ToHex()
                )  # Приватний ключ у hex
                public_key = bip44_acc_ctx.PublicKey().RawCompressed().ToHex()
                print(
                    f"Mnemonic: {mnemonic_phrase} -> Solana Address: {solana_address}\n"
                )
                with lock:
                    with open("RESULT!.txt", "a") as res:
                        res.write(
                            f"Mnemonic: {mnemonic_phrase} -> Solana Address: {solana_address}\nPrivate key: {private_key}\n Public key: {public_key}"
                        )

            with counter_lock:
                if count_speed:
                    iteration_counter += 1

    except KeyboardInterrupt:
        print("Interrupted via Ctrl+C")


if __name__ == "__main__":
    try:
        num_threads = int(input("How many threads to use? "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        exit(1)
    print(f"Threads using: {num_threads}")
    print('To show speed type "speed". To stop type "stop"')

    with open("sol_addresses.txt", "r") as addr:
        addresses = frozenset(addr.read().splitlines())

    lock = threading.Lock()

    listener_thread = threading.Thread(target=listen_for_stop, daemon=True)
    listener_thread.start()

    threads = []

    for _ in range(num_threads):
        t = threading.Thread(target=worker_thread, args=(addresses, lock), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
