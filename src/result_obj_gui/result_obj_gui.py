#! /usr/bin/env python3
import justpy as jp


def add_navigation(parent, items):
    div = jp.Div(a=parent)
    div_ul_container = jp.Div(
        a=div,
        classes="sticky top-0 mt-20 w-32 pl-3 pt-2 text-sm rounded-lg shadow-md bg-white",
    )

    ul = jp.Ul(a=div_ul_container, classes="nav")

    for name, link in items:
        if not link.startswith("#"):
            link = "#" + link

        li = jp.Li(a=ul, classes="py-1")
        jp.A(a=li, classes="nav-link", href=link, text=name)  # , scroll=True


def add_section(name):
    section_id = name.replace(" ", "-")
    section = jp.Section(
        id=section_id,
        classes="overflow-hidden rounded-lg shadow-md bg-white hover:shadow-xl transition-shadow duration-300 ease-in-out p-4",
    )
    section.add(jp.H3(classes="text-xl font-semibold pb-3", text=name))

    return section


def hello_world():
    wp = jp.WebPage()
    div_container = jp.Div(classes="md:container md:mx-auto")
    wp.add(div_container)

    div_nav = jp.Div(a=div_container, classes="min-h-screen flex flex-row bg-gray-100")

    items = [
        ("Test", "#test"),
        ("Another", "#another"),
    ]
    add_navigation(div_nav, items)

    div_content = jp.Div(a=div_nav, classes="p-3")

    section_title = jp.Section(a=div_content)
    h1 = jp.H1(a=section_title, classes="text-2xl p-4 text-center")
    h1.add(jp.Code(text="result_obj"))
    h1.add(jp.Span(text=" info"))

    sec = add_section("Test")
    sec.add(
        jp.P(
            text="""Lorem ipsum dolor sit amet, consectetur adipisicing elit. Labore earum natus vel
                    minima quod error maxime, molestias ut. Fuga dignissimos nisi nemo necessitatibus
                    quisquam obcaecati et reiciendis quaerat accusamus numquam."""
        )
    )
    div_content.add(sec)

    return wp


jp.justpy(hello_world)
