#!/usr/bin/env python
import random
import argparse

from tqdm import trange


class Minion:
    _id_counter = 1

    def __init__(self, attack, health, name=None, divine_shield=False, poison=False):
        self.attack = attack
        self.health = health
        self.name = name if name else self.generate_default_name()
        self.divine_shield = divine_shield
        self.has_attacked = False
        self.poison = poison

    @classmethod
    def generate_default_name(cls):
        default_name = f"m{cls._id_counter}"
        cls._id_counter += 1
        return default_name

    def attack_minion(self, other):
        attack_resolution_log(self, other)
        if other.divine_shield and self.attack > 0:
            other.divine_shield = False
        else:
            if self.poison and self.attack > 0:
                other.health = 0
            else:
                other.health -= self.attack

        if self.divine_shield and other.attack > 0:
            self.divine_shield = False
        else:
            if other.poison and other.attack > 0:
                self.health = 0
            else:
                self.health -= other.attack

        self.has_attacked = True

        return self.health <= 0 or other.health <= 0


def board_state(minions):
    """Return a string representation of the current board state."""
    return " ".join(
        [f"{m.attack}/{m.health}{'d' if m.divine_shield else ''}" for m in minions]
    )


def induce_of_insanity(minions):
    while len(minions) > 1:
        attackers = [m for m in minions if not m.has_attacked]
        if not attackers:
            break

        attacker = random.choice(attackers)
        target = random.choice([m for m in minions if m != attacker])

        minion_died = attacker.attack_minion(target)
        if minion_died:
            minions = [m for m in minions if m.health > 0]

        board_state_log(minions)

    return minions


def minion_from_args(args):
    minions = []
    i = 0
    while i < len(args):
        atk = int(args[i])
        hp = int(args[i + 1])

        poison = False
        divine_shield = False
        i += 2

        while i < len(args) and args[i] in ["p", "d"]:
            if args[i] == "p":
                poison = True
            elif args[i] == "d":
                divine_shield = True
            i += 1

        minions.append(Minion(atk, hp, divine_shield=divine_shield, poison=poison))
    return minions


def attack_resolution_log(attacker, target):
    """Print attack resolution when logging is enabled."""
    if args.log:
        print(f"{attacker.name} -> {target.name}")


def board_state_log(minions):
    """Print board state when logging is enabled."""
    if args.log:
        print(board_state(minions))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Hearthstone combat effects.")
    parser.add_argument(
        "minion_specs",
        nargs="+",
        help="Minion specs: atk, hp, and optionally 'd' for Divine Shield and 'p' for Poison. E.g., '4 2 d 2 2 p'",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Activate logging for attack resolutions and board states.",
    )
    args = parser.parse_args()

    simulations = 1 if args.log else 1_000_000

    total_remaining_minions = 0
    total_remaining_health = 0
    remaining_minions_count = {}

    clearances = 0
    total_remaining_minions_non_clearance = 0
    total_remaining_health_non_clearance = 0

    fmt = "Calculating... |{bar}|{percentage:3.0f}% "

    for _ in (pbar := trange(simulations, bar_format=fmt)):
        Minion._id_counter = 1
        minions = minion_from_args(args.minion_specs)

        remaining_minions = induce_of_insanity(minions)
        if not remaining_minions:
            clearances += 1
        else:
            total_remaining_minions_non_clearance += len(remaining_minions)
            total_remaining_health_non_clearance += sum(
                [m.health for m in remaining_minions]
            )

        for minion in remaining_minions:
            name = minion.name
            remaining_minions_count[name] = remaining_minions_count.get(name, 0) + 1

    if not args.log:
        non_clearance_cases = simulations - clearances
        if non_clearance_cases > 0:
            average_remaining_minions_non_clearance = (
                total_remaining_minions_non_clearance / non_clearance_cases
            )
            average_remaining_health_non_clearance = (
                total_remaining_health_non_clearance / non_clearance_cases
            )
        else:
            average_remaining_minions_non_clearance = 0
            average_remaining_health_non_clearance = 0

        clearance_probability = clearances / simulations

        print(f"Clearance Chance: {clearance_probability:.1%}")
        print(f"ø Remaining Minions: {average_remaining_minions_non_clearance:.2f}")
        print(f"ø Remaining Health:  {average_remaining_health_non_clearance:.2f}")

        sorted_minions = sorted(
            remaining_minions_count.items(), key=lambda x: x[1], reverse=True
        )

        for minion_name, count in sorted_minions:
            survival_probability = count / simulations
            survival_probability_no_clearance = count / non_clearance_cases

            print(
                f"{minion_name}: {survival_probability_no_clearance:.1%} ({survival_probability:.1%})"
            )

        if len(sorted_minions) == 0:
            print("All minions die safely.")
