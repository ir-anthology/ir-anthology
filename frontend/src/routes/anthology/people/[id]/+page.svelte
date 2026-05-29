<script lang="ts">

    const {data} = $props()
    const pubs = data.pubs
    console.log(pubs)
</script>

{#each pubs as pub (pub)}
    {pub.year} {pub.title}  DOI:{pub.doi} DBLP:{pub.pub} Auhtors:{pub.name}
    <br>
{/each}