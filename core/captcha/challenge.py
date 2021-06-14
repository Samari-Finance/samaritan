import random

from PIL import ImageDraw, ImageFont
from PIL import Image

colors = ["black", "red", "blue", "green", (64, 107, 76), (0, 87, 128), (0, 3, 82)]
fill_color = [(64, 107, 76), (0, 87, 128), (0, 3, 82), (191, 0, 255), (72, 189, 0), (189, 107, 0), (189, 41, 0)]

multiplier = 2.9
font_size = int(multiplier * 0.7 * 18)
image_pixels = (int(multiplier * 90), (int(multiplier * 60)))
get_it_max_pixels = image_pixels[0] - 5, image_pixels[1] - 5
text_size = int(20 * multiplier)
text_placement = int(20 * multiplier)
lines_min = int(6 * multiplier)
lines_max = int(11 * multiplier)
points_min = int(11 * multiplier)
points_max = int(50 * multiplier)


class Challenge:
    def __init__(self):
        self._a = 0
        self._b = 0
        self._op = '+'
        self._ans = 0
        self._choices = []
        self.new()

    def __str__(self):
        return '{a}{op}{b}=?'.format(a=self._a, b=self._b, op=self._op)

    def new(self):
        operation = random.choice(['+', '-', '×', '÷'])
        a, b, ans = 0, 0, 0
        if operation in ['+', '-']:
            a, b = random.randint(0, 50), random.randint(0, 50)
            a, b = max(a, b), min(a, b)
            ans = a+b if operation == '+' else a-b
        elif operation == '×':
            a, b = random.randint(0, 9), random.randint(0, 9)
            ans = a*b
        elif operation == '÷':
            a, b = random.randint(0, 9), random.randint(1, 9)
            ans = a
            a = a*b

        cases = 9
        choices = random.sample(range(100), cases)
        if ans not in choices:
            choices[0] = ans
        random.shuffle(choices)
        # Some bots just blindly click the first button
        if choices[0] == ans:
            choices[0], choices[1] = choices[1], choices[0]

        self._a, self._b = a, b
        self._op = operation
        self._ans = ans
        self._choices = choices

    def gen_captcha_img(self) -> Image:
        """Generates captcha image with random lines and points using pillow.

        :return: captcha image
        """
        def get_it():
            return random.randrange(5, get_it_max_pixels[0]), random.randrange(5, get_it_max_pixels[1])

        # create a img object
        img = Image.new('RGB', image_pixels, color="white")
        draw = ImageDraw.Draw(img)

        # get challenge string
        captcha_str = self.qus()

        # get the text color
        text_colors = random.choice(colors)
        font_name = "assets/fonts/SansitaSwashed-VariableFont_wght.ttf"
        font = ImageFont.truetype(font_name, random.randint(int(font_size * 0.7), int(font_size * 1.2)))
        draw.text((
            random.randint(int(text_placement * 0.7), int(text_placement * 1.2)),
            int(text_placement * 0.7), int(text_placement * 1.2)),
            captcha_str,
            fill=text_colors,
            font=font)

        # draw random lines
        for i in range(5, random.randrange(lines_min, lines_max)):
            draw.line((get_it(), get_it()), fill=random.choice(fill_color), width=random.randrange(1, 3))

        # draw random points
        for i in range(10, random.randrange(points_min, points_max)):
            draw.point((get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it(),
                        get_it(), get_it()),
                       fill=random.choice(colors))

        return img

    def qus(self):
        return self.__str__()

    def ans(self):
        return self._ans

    def choices(self):
        return self._choices
