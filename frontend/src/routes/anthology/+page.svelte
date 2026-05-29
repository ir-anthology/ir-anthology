<script lang="ts">
    let {data} = $props();
    const venues = data.venues
    const NUM_COLS = 60
    const indicies = [...Array(NUM_COLS).keys()].map((x) => {
        return Math.abs(x - NUM_COLS) + 2029 - NUM_COLS
    })
    const TABLE_HEADERS = ["Venue", "2029 - 2020", "2019-2010", "2009-2000", "1999-1990", "1989 and older"]
</script>

<table class="min-w-full divide-y divide-gray-200 table-fixed">
    <thead class="bg-gray-50 divide-x divide-gray-600">
        <tr class="divide-x divide-gray-600">
            {#each TABLE_HEADERS as header (header)}
                {#if header === "Venue"}
                    <th class="px-2 py-1 w-20">{header}</th>
                {:else}
                    <th scope="col" colspan="10" class="px-2 py-1">
                        {header}
                    </th>
                {/if}
            {/each}
        </tr>
    </thead>
    <tbody>
        {#each venues as venue, i (venue)}
            <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td class="px-4 py-3 text-sm text-gray-900 wrap-break-word w-24">
                    <!--<a href={data[label].URI}>{getShortHand(label)}</a>-->
                    <a href={"/anthology/venues/"+venue.id}>{venue.label}</a>
                </td>
                {#each indicies as index, j (index)}
                    {@const border = j % 10 === 0 ? 'border-l border-gray-600' : ''}
                    {#if venue.years.includes(index.toString())}
                        <td class="px-0.5 {border}">
                            <a href={"/anthology/venues/"+venue.id+"/"+index}>{index % 100}</a>
                        </td>
                    {:else}
                        <td class="px-0.5 {border}"></td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>