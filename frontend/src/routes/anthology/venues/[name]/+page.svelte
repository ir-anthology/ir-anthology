<script lang="ts">
    import { resolve } from '$app/paths';
    import { getIDFromURI } from '$lib/helperFunctions';

    const {data} = $props();
</script>

<h1>{data.name}</h1>
{#each data.years as year, i (i)}
    <a href={resolve(`/anthology/venues/${data.venue_id}/${year}`)}>{year}</a> <a href={resolve(`/anthology/publications/${getIDFromURI(data.uris[i])}`)}>{data.titles[i]}</a>
    <br>
{/each}