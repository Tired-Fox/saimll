# Simple Inline Markup Language and Logging (saimll)

## SAIML

This allows the user to customize strings and prettyprint different information to stdout.

Includes:
* parse -> returns formatted strings
* print -> parse SAIML markup strings and display them to stdout

Syntax:
Brackets `[]` indicate a macro. Macros can do 1 of three things; Assign a foreground/background color,
create a hyperlink, and call a builtin function. All macros will ignore extra whitespace and focus on the identifiers; `@`, `~`, and `^`.
1. Colors
    * Colors start with a leading identifier `@`. To indicate foreground or background use the specifier `F` and `B` respectively.
    Following the `@` and the specifier you can then enter the color. 
        * This can be a predifined color such as; black, red, green, yellow, blue, magenta, cyan, white. `[@F black]`.
        * It can be a hex code `#ead1a8`. `[@F #ead1a8]`.
        * It can be a XTerm code 0-256. `[@F 9]`.
        * Lastely, it can be an rgb color where the 3 numbers can be seperated by a `,` or a `;`. `[@F 114;12,212]`.
    * Colors can be reset with `[@F]` or `[@B]` to reset foreground or background respectively or `[@]` can be use to reset both.
    * Foreground and background can be specified in the same macro `[@F 1 @B 2], but they can not be reset in the same macro `[@F @B]`, use `[@]` instead.
    * While the macro will ignore white space and you can do something like `[@F#ead1a8@B3]` it is preferred to use whitespace for readability `[@F #ead1a8 @B 3]`.
2. Hyperlinks
    * Hyperlinks start with a leading identifier `~`.
    * Hyperlinks will surround plain text blocks. `[~https://example.com]Example` -> ``Example``.
        *   Links end on the next macro with the simpl `~` or at the end of the string
            * `[~https://example.com]Example[~] Not part of the link` → ``Example` Not part of the link`
            * `[~https://example.com]Link1 [~https://example.com]Link2` → ``Link1 ``link2``
            
3. Builtin functions
    * Builtin functions start with the identifier `^`. The text block following the function will have it's string value passed as a parameter.
    * You can also specify your own function or override the provided ones by calling SAIML.define("Macro Name", Callable)
    * The custom function needs to take a string and return a string. If it does not return a string it will not have an affect.
        * Example:
            ```python
            def hello_world(string: str) → str:
                return "Hello World"
            
            SAIML.define("hw", hello_world)
            SAIML.print("[^hw]Cat goes moo")
            ```
        * The above example lets SAIML know about the function hello_world and says it can be called with `hw`
        * Then all that needs to happen is to call it with `[^hw]`
    * Example:
        * `[^rainbow]Rainbow Text` will return the string with a rainbow foreground color.
SAIML also follows some inspiration from markdown where `*` means toggle bold and `_` means to toggle underline.
To reset all attributes, color and formatting, use the empty brackets `[]`.

Check out this [example](https://github.com/Tired-Fox/simll/blob/master/examples/basics.py) for how SAIML can be used
