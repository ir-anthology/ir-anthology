<script lang="ts">
    import { page } from '$app/state';
    import { resolve } from '$app/paths';
</script>

<div class="flex flex-col items-center justify-center text-center py-12 md:py-24 gap-4">
    <p class="text-sm font-medium tracking-wider text-gray-400 uppercase">Error {page.status}</p>
    <h1 class="text-2xl font-semibold text-gray-900">{page.error?.message ?? 'Something went wrong'}</h1>
    <a href={resolve('/')} class="btn-outline mt-2">Back to home</a>
</div>
