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
                link = line[9:-6]
            elif line == "## Exercices" :
                step = "exercises"
                level = []
            else :
                levels.append(line)

        elif step == "exercises" :
            if line.startswith("### Level") :
                levels.append(level)
                level = []
            elif line == "### Commentaires" :
                step = "coms"
            else :
                level.append(line)
        
        elif step == "coms" :
            coms.append(line)
    
    levels.append(level)
    levels.pop(0)

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
    
    embed.add_field(
        name="Commentaires",
        value="\n".join(coms),
        inline=False
    )
    
    return embed