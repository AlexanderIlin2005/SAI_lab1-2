import subprocess
import re
import os
import signal
import sys


class SimplePrologExecutor:
    def __init__(self, prolog_file):
        self.prolog_file = os.path.abspath(prolog_file)
        self.process = None

    def execute_query(self, prolog_query):
        commands = [
            f'consult("{self.prolog_file}").',
            f'({prolog_query}), format("RESULT: "), writeq(X), format("~n"), fail.',
            'format("END").',
            'halt.'
        ]

        full_script = '\n'.join(commands)

        try:
            self.process = subprocess.Popen(
                ['swipl', '-q'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = self.process.communicate(input=full_script, timeout=10)
            return self._parse_output(stdout)

        except subprocess.TimeoutExpired:
            if self.process:
                self.process.terminate()
            return "Таймаут запроса"
        except Exception as e:
            if self.process:
                self.process.terminate()
            return f"Ошибка: {e}"
        finally:
            self.process = None

    def _parse_output(self, output):
        if not output:
            return "Нет результатов"

        lines = []
        for line in output.strip().split('\n'):
            if line.startswith('RESULT: '):
                result = line[8:].strip()
                if result and result != 'false':
                    formatted_result = self._format_result(result)
                    lines.append(f"  {formatted_result}")

        return '\n'.join(lines) if lines else "Нет результатов"

    def _format_result(self, result):
        if result.startswith('class_boss_weapon('):
            match = re.match(r'class_boss_weapon\(([^,]+),([^,]+),([^)]+)\)', result)
            if match:
                class_name, boss, weapon = match.groups()
                return f"Класс: {class_name}, Босс: {boss}, Оружие: {weapon}"

        elif result.startswith('info('):
            match = re.match(r'info\(([^,]+),([^,]+),([^)]+)\)', result)
            if match:
                item, prop1, prop2 = match.groups()
                return f"{item}: {prop1}, {prop2}"

        return result

    def cleanup(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None


class QueryParser:
    TEMPLATES = [
        (r'классы для (.+)', 'рекомендовать_класс({}, X)'),
        (r'оружие для (.+)', 'рекомендовать_оружие_для_стиля({}, X)'),
        (r'заклинания для (.+)', 'рекомендовать_заклинания_для_стиля({}, X)'),
        (r'боссы для (новичок|начинающий)', 'рекомендовать_стартового_босса(X)'),
        (r'боссы для (опытный|эксперт)', 'рекомендовать_сложного_босса(X)'),
        (r'все классы', 'класс(X)'),
        (r'все боссы', 'босс(X)'),
        (r'все оружие', 'оружие(X)'),
        (r'все стили', 'стиль_игры(X)'),
        (r'все заклинания', 'заклинание(X)'),
    ]

    @classmethod
    def parse_to_prolog(cls, user_input):
        user_input_lower = user_input.lower().strip()

        if 'класс с' in user_input_lower:
            match = re.match(r'класс с (.+)', user_input_lower)
            if match:
                attrs = match.group(1).split(' и ')
                conditions = ', '.join([f'имеет_атрибут(X, {attr.strip()})' for attr in attrs])
                return f'класс(X), {conditions}'

        if 'рекомендация для новичка' in user_input_lower:
            return 'рекомендовать_для_новичка(Class, Boss, Weapon), X=class_boss_weapon(Class,Boss,Weapon)'

        if 'инфо о классах' in user_input_lower or 'информация о классах' in user_input_lower:
            return 'класс(Class), предпочитает_стиль(Class, Style), имеет_атрибут(Class, Attr), X=info(Class,Style,Attr)'

        if 'инфо о боссах' in user_input_lower or 'информация о боссах' in user_input_lower:
            return 'босс(Boss), находится_в(Boss, Location), сложность(Boss, Difficulty), X=info(Boss,Location,Difficulty)'

        for pattern, prolog_template in cls.TEMPLATES:
            match = re.match(pattern, user_input_lower)
            if match:
                if '{}' in prolog_template:
                    processed_groups = [group.replace(' ', '_') for group in match.groups()]
                    return prolog_template.format(*processed_groups)
                else:
                    return prolog_template

        keyword_queries = {
            'класс': 'класс(X)',
            'босс': 'босс(X)',
            'оружие': 'оружие(X)',
            'стиль': 'стиль_игры(X)',
            'заклинание': 'заклинание(X)'
        }

        for keyword, query in keyword_queries.items():
            if keyword in user_input_lower:
                return query

        return 'рекомендовать_для_новичка(Class, Boss, Weapon), X=class_boss_weapon(Class,Boss,Weapon)'


def signal_handler(sig, frame):
    print("\nЗавершение работы...")
    if 'prolog' in globals():
        prolog.cleanup()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    prolog_file = "labprolog.pl"

    if not os.path.exists(prolog_file):
        print(f"Файл {prolog_file} не найден!")
        return

    global prolog
    prolog = SimplePrologExecutor(prolog_file)

    examples = [
        "классы для ближний бой",
        "оружие для магия",
        "боссы для новичок",
        "класс с сила и телосложение",
        "инфо о классах",
        "все классы",
        "рекомендация для новичка",
        "выход"
    ]

    print("Система рекомендаций Elden Ring")
    print("Система готова к работе!")
    print("\nПримеры запросов:")
    for example in examples:
        print(f"  {example}")

    try:
        while True:
            user_input = input("\nВаш запрос: ").strip()

            if user_input.lower() in ['выход', 'exit', 'quit']:
                print("До свидания!")
                break

            if not user_input:
                continue

            if user_input.lower() == 'примеры':
                print("\nПримеры запросов:")
                for example in examples:
                    print(f"  {example}")
                continue

            prolog_query = QueryParser.parse_to_prolog(user_input)
            print(f"Prolog запрос: {prolog_query}")

            result = prolog.execute_query(prolog_query)
            print(f"\nРезультат:\n{result}")

    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        prolog.cleanup()


if __name__ == "__main__":
    main()