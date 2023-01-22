import datetime
import locale

import jinja2
import yaml


class DeferredDict:
    """A dict that uses a different dict to search for missing keys. It is
    used to implement the variable inheritance.
    """

    def __init__(self, data, parent_data):
        """Creates a new DeferredDict from the given data and parent data."""
        self.data = data
        self.parent_data = parent_data

    def __getitem__(self, key):
        """Returns the value for the given key. If the key is not found in
        the data, it will be searched in the parent data.
        """
        if key in self.data:
            return self.data[key]
        return self.parent_data[key]


WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class WeekdayTask:
    """Represents a task that happens on a specific weekday. It has a start
    time and an end time, and extra variables. If a variable is not found in
    the task, it will be searched in the parent data
    """

    def __init__(
        self,
        weekday: str,
        data: dict,
        parent_data: dict,
        week_offset: int = 0,
        locale: str = "en_US",
    ):
        """Creates a new task from the given data. It will search for the
        variables in the parent data if they are not found in the task data.
        """
        self.start_time: str = data.get("start_time", "00:00")
        self.end_time: str = data.get("end_time", "00:00")
        self.variables = DeferredDict(
            data.get("variables", {}), parent_data["variables"]
        )
        self.weekday = weekday
        self.week_offset = week_offset
        self.locale = locale

    @property
    def formatted_date(self) -> str:
        """Returns the text representation of the task. It uses the given
        language and week offset to format the task.
        """

        today = datetime.date.today()

        # Specified week
        week = today + datetime.timedelta(weeks=self.week_offset)

        # First day of the week
        first_day = week - datetime.timedelta(days=week.weekday())

        # Map self.weekday to a number
        weekday = WEEKDAY_MAP[self.weekday]

        # The date of the task
        date = first_day + datetime.timedelta(days=weekday)

        locale.setlocale(locale.LC_ALL, self.locale)

        # Format the date in the given language, the format should be like
        # "Monday, 1 January"
        date_text = date.strftime("%A, %-d %B")

        # Set the first letter to uppercase
        date_text = date_text[0].upper() + date_text[1:]

        return date_text


def render_template(
    template: str, data: dict, locale: str = "en_US.UTF-8", week_offset: int = 0
):
    """Renders a Jinja2 template with the given data. It processes the data,
    by creating the tasks and setting their names.

    Parameters
    ----------
    template : str
        The template to render
    data : dict
        The data to render the template with
    locale : str, optional
        The locale to use, by default "en_US"
    week_offset : int, optional
        The offset of the week to render, by default 0
    """

    tasks_descriptors = data["week_tasks"]

    # Create the tasks
    week_tasks = [
        WeekdayTask(key, value, data, week_offset, locale)
        for key, value in tasks_descriptors.items()
    ]

    variables = data["variables"]

    # Render the template
    template_ob = jinja2.Template(template)

    return template_ob.render(
        week_tasks=week_tasks,
        variables=variables,
        len=len,
    )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t", "--template", type=argparse.FileType("r"), help="template file"
    )
    parser.add_argument("-d", "--data", type=argparse.FileType("r"), help="data file")
    parser.add_argument(
        "-l", "--locale", type=str, default="es_ES.UTF-8", help="locale to use"
    )
    parser.add_argument("-o", "--offset", type=int, default=0, help="week offset")

    args = parser.parse_args()

    if args.template is None:
        parser.error("template file is required")

    if args.data is None:
        parser.error("data file is required")

    # Load the data from the YAML file
    data = yaml.safe_load(args.data)

    # Load the template
    template = args.template.read()

    # Render the template
    rendered = render_template(
        template, data, locale=args.locale, week_offset=args.offset
    )

    print(rendered)
