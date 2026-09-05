import { RecipeEditor } from "@/components/recipe-editor";

export default async function EditRecipePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <RecipeEditor mode="edit" recipeId={Number(id)} />;
}