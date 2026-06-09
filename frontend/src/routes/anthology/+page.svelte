<script lang="ts">
    import { resolve } from '$app/paths';
    let {data} = $props();
    const venues = $derived(data.venues)
    const conferences = $derived(venues.filter(v => v.type === 'Conference').sort((a, b) => a.label.localeCompare(b.label)))
    const journals = $derived(venues.filter(v => v.type === 'Journal').sort((a, b) => a.label.localeCompare(b.label)))
    const NUM_COLS = 60
    const indicies = [...Array(NUM_COLS).keys()].map((x) => {
        return Math.abs(x - NUM_COLS) + 2029 - NUM_COLS
    })
    const TABLE_HEADERS = ["Venue", "2029 - 2020", "2019-2010", "2009-2000", "1999-1990", "1989 and older"]
</script>

{#snippet venueTable(rows: typeof venues)}
<div class="overflow-x-auto">
<table class="min-w-full divide-y divide-gray-200 table-fixed border border-gray-300">
    <thead class="bg-gray-50 divide-x divide-gray-600">
        <tr class="divide-x divide-gray-300">
            {#each TABLE_HEADERS as header (header)}
                {#if header === "Venue"}
                    <th class="px-2 py-1 w-20 sticky left-0 z-10 bg-gray-50">{header}</th>
                {:else}
                    <th scope="col" colspan="10" class="px-2 py-1">
                        {header}
                    </th>
                {/if}
            {/each}
        </tr>
    </thead>
    <tbody>
        {#each rows as venue, i (venue)}
            <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td class="px-4 py-3 text-sm text-gray-900 wrap-break-word w-24 sticky left-0 z-10" class:bg-white={i % 2 === 0} class:bg-gray-50={i % 2 !== 0}>
                    <a href={resolve(`/anthology/venues/${venue.id}`)} class="link font-bold">{venue.label}</a>
                </td>
                {#each indicies as index, j (index)}
                    {@const border = j % 10 === 0 ? 'border-l border-gray-300' : ''}
                    {#if venue.years.includes(index.toString())}
                        <td class="px-0.5 {border}">
                            <a href={resolve(`/anthology/venues/${venue.id}/${index}`)} class="link">{String(index % 100).padStart(2, '0')}</a>
                        </td>
                    {:else}
                        <td class="px-0.5 {border}"></td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>
</div>
{/snippet}

<h1 class="text-2xl mb-4">Venues</h1>

<h2 class="text-xl font-semibold mb-2">Conferences</h2>
{@render venueTable(conferences)}

<h2 class="text-xl font-semibold mt-6 mb-2">Journals</h2>
{@render venueTable(journals)}
