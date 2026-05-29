<script lang="ts">
    import { resolve } from '$app/paths';
    import { page } from '$app/state';
    import { getIDFromURI } from '$lib/helperFunctions';
    const year = page.url.pathname.split("/").at(-1)
    const {data} = $props();

</script>
{#if Object.keys(data).includes("articles")}
    {@const articles = data["articles"]}
    {#each articles?.keys() as volume (volume)}
        {@const volumes = articles?.get(volume)}
        {#each volumes?.keys() as issue (issue)}
            {@const entries = volumes?.get(issue)}
            {year} Volume {volume} Issue {issue}
            <br>
            {#each entries as entry (entry)}
                DOI: {entry.doi} dblp:{entry.pub} <a href={resolve(`/anthology/publications/${getIDFromURI(entry.pub)}`)}> {entry.title} </a>
                <br>
            {/each}
            <br>
        {/each}
        <br>
    {/each}
{:else}
    {#each data.proceedings as proceeding (proceeding)}
        <h1>{proceeding.title}</h1>
        Anthology ID: MISSING
        <br>
        Year: {proceeding.year}
        <br>
        Venue: <a href={resolve(`/anthology/venues/${proceeding.name}`)}>{proceeding.name}</a>
        <br>
        Publisher: {proceeding.publisher}
        <br>
        URL: {proceeding.url}<!--Replace with DBLP-URL-->
        <br>
        DOI: {proceeding.doi}
        <br>
        DBLP: {proceeding.pub}<!--Replace with DBLP-URL-->
        <br>
        BibTeX: TODO
        <!--Show Papers from that year-->
        <br>
        {#each data.inproceedings[proceeding.pub] as inproceeding (inproceeding)}
            <a href={resolve(`/anthology/publications/${inproceeding.id}`)}>{inproceeding.title}</a> {inproceeding.pub}
            <br>
        {/each}
        <br>
        <br>
    {/each}
{/if}


