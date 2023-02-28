import discord

def embed(markdown: str) -> discord.Embed :
    step = "title"
    title = ""
    link = ""
    description = []
    levels = []
    coms = []
    for line in markdown.split('\n') :
        if step == "title" :
            if line.startswith("# ") :
                title = line[2:]
            elif line.lower().startswith("[slides]") :
                link = line.removesuffix("</br>")[9:-1]
            elif line == "## Exercices" :
                step = "exercises"
                level = []
            else :
                description.append(line)

        elif step == "exercises" :
            if line.startswith("### L") :
                levels.append(level)
                level = []
            elif line == "### Commentaires" :
                step = "coms"
            elif line not in {"", " ", "\n"} :
                level.append(line)
        
        elif step == "coms" :
            coms.append(line)
    
    levels.append(level)

    embed = discord.Embed(
        title=title,
        url=link,
        description='\n'.join(description),
    )

    for i in range(1, len(levels)) :
        embed.add_field(
            name=f"Level {i}",
            value='\n'.join(levels[i]),
            inline=False
        )
    
    if len(coms) > 0 :
        embed.add_field(
            name="Commentaires",
            value="\n".join(coms),
            inline=False
        )
    
    return embed

def embed_help(dir_: str) -> discord.Embed :
    File = open("fixed_data/" + dir_)
    lines = File.read().split('\n')
    File.close()
    
    title = "Dijkstra-Chan's Commands :"

    categories: dict[str, list[str]] = {}
    cat = ""

    for line in lines :
        if line.startswith("# ") :
            cat = line[2:]
            categories[cat] = []
        else :
            categories[cat].append(line)
    
    embed = discord.Embed(title=title)

    for cat_name, cat_lines in categories.items() :
        while cat_lines[-1] == "" :
            cat_lines.pop()
        embed.add_field(
            name=cat_name,
            value='\n'.join(cat_lines),
            inline=False
        )
    
    return embed